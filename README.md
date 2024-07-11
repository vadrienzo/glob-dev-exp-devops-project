# Global Dev Experts DevOps Project

Global Dev Experts DevOps Project

## Database connection

In order to connect to the database, you need to have a MySQL server running. You can run a MySQL server using Docker with the following command:

```bash
docker run --name mysql -v $(pwd):/var/lib/mysql -e MYSQL_ROOT_PASSWORD=mysql \
-e MYSQL_DATABASE=project -e MYSQL_USER=$(DB_USER_NAME) -e MYSQL_PASSWORD=$(DB_PASSWORD) \
-p 5001:5001 -d mysql:8.0.34
```

make sure to replace `$(DB_USER_NAME)` and `$(DB_PASSWORD)` with your desired username and password.
