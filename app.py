import mysql.connector
import time
import threading


def query_database():
    # Conectar a la base de datos
    db = mysql.connector.connect(
    host="localhost",
    port="3333",
    user="root",
    password="123456",
    database="mydb"
    )

    # Crear un cursor para ejecutar consultas SQL
    cursor = db.cursor()

    idx = 0
    while True:
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
        time.sleep(2)
    # Cerrar la conexión y el cursor
    cursor.close()
    db.close()

mi_hilo = threading.Thread(target=query_database)
mi_hilo.start()
mi_hilo.join()