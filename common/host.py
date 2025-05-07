import os
import socket

def host_send( cmd ):
    if os.path.exists("/var/run/host.sock"):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect("/var/run/host.sock")
            s.sendall(cmd.encode())
            response = s.recv(4096).decode()

            s.close()
            return [ True, response ]
        except Exception as e:
            return [ False, f"Fail Socker Connect: {e}" ]
    else:
        return [ False, "Not exist Socker file" ]

def create_caddy_file( domain, admin_port, user_port ):
    return f"""
:{admin_port} {{
    
    root * /etc/caddy/CBT/{domain}/FE_ADMIN

    route {{
        reverse_proxy /api/* {domain}_be:4000
        reverse_proxy /data/* {domain}_be:4000
        try_files {{path}} /index.html
        file_server
    }}
}}

:{user_port} {{
    
    root * /etc/caddy/CBT/{domain}/FE_USER

    route {{
        reverse_proxy /api/* {domain}_be:4000
        reverse_proxy /data/* {domain}_be:4000
        try_files {{path}} /index.html
        file_server
    }}
}}

http://admin.{domain}.testsimprec.duckdns.org {{
    root * /etc/caddy/CBT/{domain}/FE_ADMIN

    route {{
        reverse_proxy /api/* {domain}_be:4000
        reverse_proxy /data/* {domain}_be:4000
        try_files {{path}} /index.html
        file_server
    }}
}}

http://user.{domain}.testsimprec.duckdns.org {{
    root * /etc/caddy/CBT/{domain}/FE_USER

    route {{
        reverse_proxy /api/* {domain}_be:4000
        reverse_proxy /data/* {domain}_be:4000
        try_files {{path}} /index.html
        file_server
    }}
}}

""".strip()


def exec_on_host(cmd: str):
    print(f"[EXEC] {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return [True, result.stdout + result.stderr]
    except Exception as e:
        return [False, str(e)]

def create_cbt_file( domain, school_name, version="" ):
    return f"""
version: '3.9'
services:
  {domain}_fe_admin:
    build:
      context: ./FE_ADMIN
      dockerfile: Dockerfile
      args:
        USER_NAME: "{school_name}"
        VERSION: "{version}"
    image: "{domain}_fe_admin"
    container_name: {domain}_fe_admin
    volumes:
      - ./../../services/CBT/{domain}/FE_ADMIN:/app/build
    networks:
      - {domain}_network
  
  {domain}_fe_user:
    build:
      context: ./FE_USER
      dockerfile: Dockerfile
      args:
        USER_NAME: "{school_name}"
        VERSION: "{version}"
    image: "{domain}_fe_user"
    container_name: {domain}_fe_user
    volumes:
      - ./../../services/CBT/{domain}/FE_USER:/app/build
    networks:
      - {domain}_network

  {domain}_be:
    build:
      context: ./BE
      dockerfile: Dockerfile
    image: "{domain}_be"
    container_name: {domain}_be
    environment:
      - SWAGGER_SCHEMES=http
      - SWAGGER_HTTP_KIND=http://
      - SWAGGER_HOST=0.0.0.0
      - SWAGGER_PORT=4000

      - DB_HOST={domain}_db
      - DB_PORT=3306
      - DB_USER=root
      - DB_PASSWORD=Ibst0552997730!
      - DB_NAME=CBT

      - MAIL_USER=ibstechco
      - MAIL_PASSWORD=ibst0552997730!
      - MAIL_USER_EMAIL=ibstechco@naver.com
      - MAIL_TEXT=localhost:8901/Result/
      - DATA_PATH=/data
      - EXCEL_PATH=/excelData
      - IMP_KEY=0588880683871737
      - IMP_SECRET=4cf0204264167f2102a9b791a3d69b6d2cb680f7cb348e89d393421335d5527c366d5b01155454da
    
    volumes:
      - ./../../services/CBT/{domain}/BE/logs:/app/logs
      - ./../../services/CBT/{domain}/BE/excelData:/app/excelData
      - ./../../services/CBT/{domain}/BE/data:/app/data
    networks:
      - caddy_network
      - {domain}_network
    depends_on:
      - {domain}_db

  {domain}_db:
    build:
      context: ./DB
    image: {domain}_db
    container_name: {domain}_db
    environment:
      MARIADB_ROOT_PASSWORD: Ibst0552997730!
      MARIADB_DATABASE: CBT
      LANG: C.UTF-8
    command: bash -c "/wait_for_afterdb.sh & docker-entrypoint.sh mysqld"
    volumes:
      - {domain}_db_data:/var/lib/mysql
      - ./../../services/CBT/{domain}/DB/:/var/log/mysql/
    networks:
      - caddy_network
      - {domain}_network

networks:
  caddy_network:
    external: true
  {domain}_network:
    driver: bridge

volumes:
  {domain}_db_data: {{}}
  {domain}_be_logs_volume: {{}}
""".strip()

def create_simprec_file( ):
    return ""
