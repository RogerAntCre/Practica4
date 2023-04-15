# Ejemplo de implementación de un Cluster MariaDB con HA_PROXY
Repositorio que muestra une ejemplo de un balanceador de carga con MariaDB y HA Proxy.

## Instalación

1.  Crea un directorio para almacenar la configuración de cada instancia de MariaDB:

```bash
mkdir mariadb-master1/
touch mariadb-master1/my.cnf
chmod 755 mariadb-master1/my.cnf

mkdir mariadb-master2/
touch mariadb-master2/my.cnf
chmod 755 mariadb-master2/my.cnf

```

2.  A continuación, modifica los archivos `my.cnf` en cada directorio de configuración con el siguiente contenido:

**~/mariadb-master1/conf/my.cnf:**

```
[mysqld]
# Habilita la funcionalidad de registro binario en el servidor MySQL.
log-bin

# Identifica de manera única el servidor MySQL en un grupo de servidores en un entorno de replicación maestro-esclavo.
# El valor debe ser único para cada servidor.
server_id=1

# Garantiza que los registros binarios se escriban en disco antes de que se confirme que se ha completado una transacción.
# Esta configuración puede afectar el rendimiento, pero es necesaria para garantizar la integridad de los datos.
sync_binlog=1

# Establece el formato de registro binario que se utilizará en el servidor MySQL.
# El formato de fila es el más detallado y se utiliza para la replicación de datos en tiempo real.
binlog_format=row

# Especifica el nombre o dirección IP del servidor MySQL para que los esclavos de replicación puedan conectarse.
# Es necesario especificar esto si se utiliza la replicación maestro-esclavo.
# Para el ejemplo se conecta al segundo nodo
report-host=mariadb-master2
```

**~/mariadb-master2/conf/my.cnf:**

```
[mysqld]
# Habilita la funcionalidad de registro binario en el servidor MySQL.
log-bin

# Identifica de manera única el servidor MySQL en un grupo de servidores en un entorno de replicación maestro-esclavo.
# El valor debe ser único para cada servidor.
server_id=2

# Garantiza que los registros binarios se escriban en disco antes de que se confirme que se ha completado una transacción.
# Esta configuración puede afectar el rendimiento, pero es necesaria para garantizar la integridad de los datos.
sync_binlog=1

# Establece el formato de registro binario que se utilizará en el servidor MySQL.
# El formato de fila es el más detallado y se utiliza para la replicación de datos en tiempo real.
binlog_format=row

# Especifica el nombre o dirección IP del servidor MySQL para que los esclavos de replicación puedan conectarse.
# Es necesario especificar esto si se utiliza la replicación maestro-esclavo.
# Para el ejemplo como es replica master-master apunta al primer nodo.
report-host=mariadb-master1
```
3. Crea una red docker para el cluster
```bash
docker network create mariadb_cluster
```

4.  Ejecuta dos contenedores de Docker con MariaDB, utilizando la configuración personalizada:

```bash
docker run --name mariadb-master1 -v $(pwd)/mariadb-master1/my.cnf:/etc/mysql/conf.d/my.cnf -e MYSQL_ROOT_PASSWORD=123456 -p 3310:3306 --net mariadb_cluster -d mariadb:10.11.2-jammy

docker run --name mariadb-master2 -v $(pwd)/mariadb-master2/my.cnf:/etc/mysql/conf.d/my.cnf -e MYSQL_ROOT_PASSWORD=123456 -p 3320:3306 --net mariadb_cluster -d mariadb:10.11.2-jammy

```

Esto iniciará dos contenedores de MariaDB con nombres `mariadb-master1` y `mariadb-master2`, usando el archivo `my.cnf` personalizado que creamos en el paso 2.

5.  A continuación, debes configurar la replicación entre las dos instancias de MariaDB. Primero, conecta al primer contenedor y crea un usuario de replicación:

Ingresamos al mysql en el nodo 1

```bash
docker exec -it mariadb-master1 mysql -uroot -p123456
```
Ejecutamos lo siguiente

```sql
CREATE USER 'repl'@'%' IDENTIFIED BY 'replpassword';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
FLUSH PRIVILEGES;

SHOW MASTER STATUS;

```

Toma nota de los valores de "File" y "Position" que se muestran en el resultado de `SHOW MASTER STATUS`. Ejemplo:

```
MariaDB [(none)]> SHOW MASTER STATUS;
+-------------------+----------+--------------+------------------+
| File              | Position | Binlog_Do_DB | Binlog_Ignore_DB |
+-------------------+----------+--------------+------------------+
| mysqld-bin.000002 |      771 |              |                  |
+-------------------+----------+--------------+------------------+
1 row in set (0.000 sec)
```


6.  Conéctate al segundo contenedor de MariaDB:

```bash
docker exec -it mariadb-master2 mysql -uroot -p123456
````

Configura la replicación:

```sql
CHANGE MASTER TO MASTER_HOST='mariadb-master1', MASTER_USER='repl', MASTER_PASSWORD='replpassword', MASTER_LOG_FILE='mysqld-bin.000002', MASTER_LOG_POS=771;

START SLAVE;

```

Reemplaza `mysqld-bin.000002` y `771` con los valores de "File" y "Position" obtenidos en el paso 5.

Para verificar que todo este bien:

```sql
SHOW SLAVE STATUS \G
```
Deben verificar que los mensajes de Error estén vacios:

```
                    Last_Errno: 0
                    Last_Error: 
```
 Si no existe errores en el nodo `mariadb-master1` cree una Base de datos y verifique como se replica.

7.  Repite los pasos 5 y 6, pero esta vez conectándote al segundo contenedor primero y luego al primero, para configurar

## Probando.

Para provar la implementación sigue los siguientes pasos.

1. Abre dos consolas de MySQL una a cada instancia del cluster.
2. En `mariadb-master1`: crea una BBDD por ejemplo: Library
3. En `mariadb-master2`: Verifica como  se creó la BBDD.
3. En `mariadb-master2`: Crea una tabla e inserta datos, puede usar el ejemplo Books de la segunda práctica.
4. En `mariadb-master1`: Verifica que la tabla se haya propagado.
5. Para el contenedor `mariadb-master2`
6. En `mariadb-master1`: Elimina los libros con Ids: 2,4,6
7. Inicia el contenedor `mariadb-master2`, verifica como las modificaciones se propagaron.

## Conectando dede un cliente.
Vamos a crear una App Python que lea del Cluster de BBDD.

Para crear un programa en Python que lea todos los libros de la tabla en una base de datos MariaDB, primero necesitamos instalar el paquete `mysql-connector-python` que nos permite conectarnos a la base de datos. Puedes instalarlo usando el siguiente comando en la terminal:

```bash
pip install mysql-connector-python

```

Luego, puedes utilizar el siguiente código Python para conectarte a la base de datos y leer todos los libros de la tabla `book`:

```python
import mysql.connector

# Conectar a la base de datos
db = mysql.connector.connect(
  host="localhost",
  port="3310",
  user="root",
  password="123456",
  database="mydb"
)

# Crear un cursor para ejecutar consultas SQL
cursor = db.cursor()

# Ejecutar una consulta SQL para obtener todos los libros
cursor.execute("SELECT * FROM book")

# Obtener todos los resultados y mostrarlos en pantalla
books = cursor.fetchall()
for book in books:
  print("Book ID:", book[0])
  print("Name:", book[1])
  print("Release Date:", book[2])
  print("Quantity:", book[3])
  print("Price:", book[4])

# Cerrar la conexión y el cursor
cursor.close()
db.close()

```

## Implementando Alta Disponibilidad desde el cliente con HA Proxy.

1.  Descargar la imagen de balanceador de carga: Vamos a utilizar HAProxy como balanceador de carga. Para obtener la imagen oficial de HAProxy, ejecuta el siguiente comando:

```bash
docker pull haproxy:2.7.6
```

6.  Crear un archivo de configuración para HAProxy: Crea un archivo llamado `haproxy.cfg` con el siguiente contenido.

```bash
global
  daemon
  maxconn 256

defaults
  mode tcp
  timeout connect 5000ms
  timeout client 50000ms
  timeout server 50000ms

frontend mariadb_frontend
  bind *:3306
  default_backend mariadb_backend

backend mariadb_backend
  balance roundrobin
  server mariadb-master1 mariadb-master1:3306 check
  server mariadb-master2 mariadb-master2:3306 check

```

7.  Iniciar el contenedor de HAProxy: Ejecuta el siguiente comando en el directorio donde se encuentra el archivo `haproxy.cfg`:

```bash
docker run -d --name haproxy --net mariadb_cluster -p 3306:3306 -v $(pwd)/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro haproxy

```

