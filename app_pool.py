
import time
import threading
import mysql.connector.pooling
config = {
  "user": "root",
  "password": "123456",
  "host": "localhost",
  "port": "3333",
  "database": "mydb"
}

def query_database():
    # Creamos pool de conexiones
    pool = mysql.connector.pooling.MySQLConnectionPool(pool_size=4, pool_name="mi_pool", pool_reset_session=True, **config)    

    idx = 0
    while True:
        # Obtener una conexion del pool
        try:
            connection = pool.get_connection()
            connection.ping(reconnect=True, attempts=3, delay=0)
            # Crear un cursor para ejecutar consultas SQL
            cursor = connection.cursor()
            current = (idx%10) + 1
            # Ejecutar una consulta SQL para obtener todos los libros
            cursor.execute("SELECT book_id, CONCAT(name, ' ', @@hostname), release_date, quantity, price FROM book WHERE book_id = %s", (current,))

            # Obtener todos los resultados y mostrarlos en pantalla
            books = cursor.fetchall()
            for book in books:
                print("Book ID:", book[0])
                print("\tName:", book[1])
                print("\tRelease Date:", book[2])
                print("\tQuantity:", book[3])
                print("\tPrice:", book[4])
                print("=====================")
            idx = idx + 1
            connection.close()
        except:
            print("Something went wrong (Dont Worry Retrying)")
        time.sleep(2)
    # Cerrar la conexión y el cursor
    cursor.close()
    db.close()

mi_hilo = threading.Thread(target=query_database)
mi_hilo.start()
mi_hilo.join()