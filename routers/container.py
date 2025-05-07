from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from models import container
from models.division import Division 
from typing import List
from schemas.container import ContainerOut, ContainerUpdate, ContainerCreate
from common.host import host_send, exec_on_host, create_caddy_file, create_cbt_file, create_simprec_file
import subprocess
import docker
from pydantic import BaseModel
from docker.errors import NotFound, APIError

docker_client = docker.from_env()

class DomainRequest(BaseModel):
    domain: str


router = APIRouter(
    prefix="/api/container",
    tags=["Container"]
)


@router.get("/active")
def get_active_containers(search: str = "", db: Session = Depends(get_db)):
    try:
        results = []

        query = db.query(
            container.Container.container_cd,
            container.Container.sch_cd,
            container.Container.sch_name,
            container.Container.sch_nickname,
            container.Container.domain,
            container.Container.grop_cd,
            container.Container.div_cd,
            Division.div_name.label("div_name")
        ).join(Division, container.Container.div_cd == Division.div_cd)\
         .filter(Division.div_yn == 0)

        if search:
            query = query.filter(container.Container.sch_name.ilike(f"%{search}%"))

        rows = query.all()

        for row in rows:
            try:
                container_obj = docker_client.containers.get(f"{row.domain}_be")
                status = container_obj.status 
            except NotFound:
                status = "not_found"
            results.append({
                "container_cd": row.container_cd,
                "sch_cd": row.sch_cd,
                "sch_name": row.sch_name,
                "sch_nickname": row.sch_nickname,
                "domain": row.domain,
                "grop_cd": row.grop_cd,
                "div_cd": row.div_cd,
                "div_name": row.div_name,
                "status": status  
            })

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{div_cd}", response_model=List[ContainerOut])
def get_containers_by_div(div_cd: int, search: str = "", db: Session = Depends(get_db)):
    query = db.query(
        container.Container.sch_cd,
        container.Container.sch_name,
        container.Container.sch_nickname,
        container.Container.domain,
        container.Container.grop_cd,
        container.Container.div_cd,
        Division.div_name.label("div_name") 
    ).join(Division, container.Container.div_cd == Division.div_cd)\
     .filter(container.Container.div_cd == div_cd)

    if search:
        query = query.filter(container.Container.sch_name.ilike(f"%{search}%"))

    return query.all()

# 컨테이너 수정
@router.put("/update/{container_cd}")
def update_container(
    container_cd: int,
    updated: ContainerUpdate,
    db: Session = Depends(get_db)
):
    db_item = db.query(container.Container).filter(container.Container.container_cd == container_cd).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="컨테이너를 찾을 수 없습니다.")

    db_item.sch_name = updated.sch_name
    db_item.sch_nickname = updated.sch_nickname
    db_item.domain = updated.domain
    db_item.grop_cd = updated.grop_cd
    db_item.div_cd = updated.div_cd

    db.commit()

    return {"success": True, "updated": updated}


# 컨테이너 추가
@router.post("/add", response_model=List[ContainerOut])
def create_container(
    new: ContainerCreate,
    db: Session = Depends(get_db)
):
    created = []

    try:
        for item in new.containers:
            print(f"[INFO] 생성 도메인: {item.domain}")
            c = container.Container(
                sch_cd=new.sch_cd,
                sch_name=new.sch_name,
                sch_nickname=new.sch_nickname,
                domain=item.domain,
                grop_cd=new.grop_cd,
                div_cd=item.div_cd
            )
            
            db.add(c)
            db.commit()  
            
            home = "/home/psy"
            admin_port = 10000 + int(c.container_cd)
            user_port = 20000 + int(c.container_cd)
            # 경로 고정 논의
            caddy_path = f"{home}/workspace/docker/services/caddy/sites/{item.domain}.caddy"
            caddy_content = create_caddy_file(item.domain, admin_port, user_port)
            host_send(f"mkdir -p $(dirname {caddy_path}) && cat <<'EOF' > {caddy_path}\n{caddy_content}\nEOF")
            
            if int(item.div_cd) == 1: # CBT
                cbt_path = f"{home}/workspace/docker/project_source/CBT/docker-compose.{item.domain}.yml"
                cbt_content = create_cbt_file( item.domain, new.sch_name )
                host_send(f"mkdir -p $(dirname {cbt_path}) && cat <<'EOF' > {cbt_path}\n{cbt_content}\nEOF")
                host_send(f"cd $(dirname {cbt_path}) && docker compose -f {cbt_path} run --rm {item.domain}_fe_admin yarn build && docker rmi {item.domain}_fe_admin")
                host_send(f"cd $(dirname {cbt_path}) && docker compose -f {cbt_path} run --rm {item.domain}_fe_user yarn build && docker rmi {item.domain}_fe_user")
                host_send(f"cd $(dirname {cbt_path}) && docker compose -f {cbt_path} up -d --build {item.domain}_be {item.domain}_db")
            elif int(item.div_cd) == 2: # SIMPREC
                simprec_path = f"{home}/workspace/docker/project_source/SIMPREC/docker-compose.{item.domain}.yml"
                simprec_content = create_simprec_file(  )
                host_send(f"mkdir -p $(dirname {simprec_path}) && cat <<'EOF' > {simprec_path}\n{simprec_content}\nEOF")
            
            subprocess.run(["docker", "exec", "caddy", "caddy", "reload", "--config", "/etc/caddy/Caddyfile"])

            # created.append(c)
        
        return created  
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="이미 존재하는 학교코드입니다.")


# 컨테이너 삭제
@router.delete("/delete", status_code=200)
def delete_containers(
    container_cd_list: List[int] = Body(...),
    db: Session = Depends(get_db)
):
    containers = db.query(container.Container).filter(container.Container.container_cd.in_(container_cd_list)).all()
    home = "/home/psy"

    for c in containers:
        domain = c.domain
        div_cd = c.div_cd

        # 1. 컨테이너 정지 및 삭제
        for name in [f"{domain}_be", f"{domain}_db"]:
            try:
                docker_cont = docker_client.containers.get(name)
                docker_cont.stop()
                docker_cont.remove(force=True)
                print(f"[INFO] 컨테이너 {name} 삭제 성공")
            except Exception as e:
                print(f"[ERROR] 컨테이너 {name} 삭제 실패: {e}")

        # 2. Compose 파일 제거
        if int(div_cd) == 1:  # CBT
            compose_path = f"{home}/workspace/docker/project_source/CBT/docker-compose.{domain}.yml"
        else:  # SIMPREC
            compose_path = f"{home}/workspace/docker/project_source/SIMPREC/docker-compose.{domain}.yml"

        compose_result = host_send(f"rm -f {compose_path}")
        print(f"[INFO] Compose 파일 삭제 결과: {compose_result}")

        # 3. Caddy 설정 제거
        caddy_path = f"{home}/workspace/docker/services/caddy/sites/{domain}.caddy"
        caddy_result = host_send(f"rm -f {caddy_path}")
        print(f"[INFO] Caddy 설정 파일 삭제 결과: {caddy_result}")

        # 4. 서비스 디렉터리 제거 (CBT or SIMPREC)
        if int(div_cd) == 1:
            service_dir = f"{home}/workspace/docker/services/CBT/{domain}"
        else:
            service_dir = f"{home}/workspace/docker/services/SIMPREC/{domain}"

        dir_result = host_send(f"rm -rf {service_dir}")
        print(f"[INFO] 서비스 디렉터리 삭제 결과: {dir_result}")

    # 5. Caddy reload
    subprocess.run(["docker", "exec", "caddy", "caddy", "reload", "--config", "/etc/caddy/Caddyfile"])
    print("[INFO] Caddy reload 완료")

    # 6. DB 삭제
    deleted_count = db.query(container.Container).filter(container.Container.container_cd.in_(container_cd_list))\
        .delete(synchronize_session=False)
    db.commit()

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="삭제할 컨테이너가 없습니다.")

    return {"success": True, "deleted": deleted_count}



# 컨테이너 정지
@router.post("/stop")
def stop_containers(payload: DomainRequest = Body(...)):
    try:
        domain = payload.domain
        containers = [
            f"{domain}_be",
            f"{domain}_db",
        ]
        for name in containers:
            try:
                container = docker_client.containers.get(name)
                container.stop()
            except NotFound:
                print(f"[WARN] 컨테이너 {name} 없음 (무시)")
        return {"message": "Containers stopped"}
    except Exception as e:
        print(f"[ERROR] Stop failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop containers: {e}")

# 컨테이너 시작
@router.post("/start")
def start_containers(payload: DomainRequest = Body(...)):
    try:
        domain = payload.domain
        containers = [
            f"{domain}_be",
            f"{domain}_db",
        ]
        for name in containers:
            try:
                container = docker_client.containers.get(name)
                container.start()
            except NotFound:
                print(f"[WARN] 컨테이너 {name} 없음 (무시)")
        return {"message": "Containers started"}
    except Exception as e:
        print(f"[ERROR] Start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start containers: {e}")
    
 # 컨테이너 로그   
@router.get("/logs/{domain}/{target}")
def get_container_logs(domain: str, target: str):
    try:
        container_name = f"{domain}_{target}"  # ex: jn-university_db
        container = docker_client.containers.get(container_name)
        logs = container.logs(tail=100).decode("utf-8")  # 최근 100줄만 가져옴
        return {"logs": logs}
    except Exception as e:
        print(f"[ERROR] Failed to fetch logs: {e}")
        raise HTTPException(status_code=404, detail="Container logs not found.")
    
    
# 서버 이름들
EXCLUDE_CONTAINERS = {"dockflow_be", "dockflow_db", "caddy"}

# 컨테이너 전체 정지
@router.post("/allstop")
def stop_all_containers():
    try:
        containers = docker_client.containers.list(all=True)
        for container in containers:
            container.reload()  # 상태 새로고침
            if container.name in EXCLUDE_CONTAINERS:
                continue 
            if container.status == "running":
                container.stop()
        return {"message": "All containers stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 컨테이너 전체 시작
@router.post("/allstart")
def start_all_containers():
    try:
        containers = docker_client.containers.list(all=True)
        for container in containers:
            container.reload()  # 상태 새로고침
            if container.name in EXCLUDE_CONTAINERS:
                continue
            if container.status != "running":
                container.start()
        return {"message": "All containers started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))