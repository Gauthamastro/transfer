import sqlite3

conn = sqlite3.connect("Test.db")

c = conn.cursor()

# Create table
c.execute('''CREATE TABLE stocks
             (date text, trans text, symbol text, qty real, price real)''')
import random, string


def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


random_text = [randomString() for i in range(10**6)]
print("Random String generated")
random_int = [str(random.randint(0,2000)) for i in range(10**6)]
print("Random String generated")
import time
print("Starting ...")
a = time.time()
for i,j in zip(random_text,random_int):
    c.execute("INSERT INTO stocks VALUES ('2006-01-05','{}','RHAT',{},35.14)".format(i,j))
print("Finished 25000 Inserts in {}".format(time.time()-a))