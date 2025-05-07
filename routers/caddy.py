from fastapi import APIRouter
import subprocess

router = APIRouter(prefix="/api/caddy", tags=["Caddy"])

@router.post("/reload")
def reload_caddy():
    try:
      
        subprocess.run(
            ["docker", "exec", "caddy", "caddy", "validate", "--config", "/etc/caddy/Caddyfile"],
            check=True
        )

        subprocess.run(
            ["docker", "exec", "caddy", "caddy", "reload", "--config", "/etc/caddy/Caddyfile"],
            check=True
        )

        return { "message": "캐디 리로드 성공" }

    except subprocess.CalledProcessError as e:
        return { "message": f"리로드 실패: {e}" }
