# -*- coding: utf-8 -*-
"""
Created on Thu Nov 22 15:57:46 2018

Software Miniproject (Coursework 8)

Database

@author: Matthew
"""
import sqlite3
import os

# Set the work directory
#os.chdir('C:/Users/Matt/OneDrive/USB Stick/Bath Uni Work/Software Technologies for Data Science/Coursework 8/till/till')    # If on PC
#os.chdir('F:/Bath Uni Work/Software Technologies for Data Science/Coursework 8/till/till')             # If on laptop and usb
#os.chdir('D:/Bath Uni Work/Software Technologies for Data Science/Coursework 8/till/till')             # If on PC and usb


# Import the data
products = open('products.txt', 'r')
#for line in products:
#    print(line)

# Create a database
db = sqlite3.connect('products.db')

# Get a cursor object
cursor = db.cursor()

# Drop the table if it already exists...
cursor.execute('DROP TABLE IF EXISTS products')
cursor.execute('DROP TABLE IF EXISTS shift')
cursor.execute('DROP TABLE IF EXISTS payment_method')

"""
Products.txt contains all the sql commands that make the tables we need
"""
for line in products:
    cursor.execute(line)

# need to add a new product which is the deals
cursor.execute("INSERT INTO products (productid, name, shift) VALUES (5001, 'Meal Deal Free Sack', 0), (5002, 'Hot Drink and Cookie', 0)")

# Need to commit the changes to the database
db.commit()

"""
Need to create a transactions table
It will have a 

orderItemId INTEGER PRIMARY KEY AUTOINCREMENT      # A unique number for each item bought
transactionId INTEGER,    # A number for the transaction. Each
itemId INTEGER,       # the product id number of that item
price FLOAT,         # the price of that item
quantity INTEGER,    # Don't know if I'll have this. Might just put it in twice...w
"""

"""
Could also create a SALE table:
    saleId              :   unique number for each item bought
    itemId              :   The unique code of the item
    refund              :   Is a 1 or 0 if a refund table was made
    totalSale           :   price of the sale
    totalPayment        :   The amount of money given in the payment??
"""


cursor.execute('DROP TABLE IF EXISTS transactions')
db.commit()
cursor.execute('DROP TABLE IF EXISTS sale')
db.commit()
cursor.execute('DROP TABLE IF EXISTS cur_transaction')
db.commit()
"""
transactions is a table that will have:
    
    A row for every transaction
    
    transactionId        :     An integer unique number for each transaction
    totCost              :     The total for that transaction
    amountGiven          :     The amount received by the cashier
    change               :     The amount of change needed to give


sale table will have:
    
    A row for every item in the transaction
    
    saleId INTEGER PRIMARY KEY AUTOINCREMENT,    : A unique integer number for each sale item
    transactionId INTEGER,                       : The transaction ID of the current transaction
    prodId INTEGER,                              : The product ID of the product selected    
    price INTEGER,                               : The price of the product ordered       
    quantity INTEGER,                            : The quantity of the product ordered
    refund INTEGER,                              : An indicator to say whether this sale was a refund or not (refund if = 4)
    mealDeal INT,                                : An indicator to say whether this sale item was a meal deal (=1) or not
    halfCookie INT,                              : An indicator to say whether this sale item was a half price cookie deal (=1) or not
    
    prodId is a foreign key from the products table
    transactionId is a foreign key from the transactions table
    
    
cur_transaction will have:
    
    A grouped by version of sale
    It will have the sum of the prices (+ and -)
    It will have the sum of the quantities (+ and -)
    This overcomes the deals issue for refunded items
    
    prodId INTEGER,                : The ID of the product ordered
    price INTEGER,                 : The price of the product ordered
    quantity INTEGER,              : The quantity of the product ordered
    
    prodId will be a foreign key from the products table
"""

cursor.execute('CREATE TABLE transactions (transactionId INTEGER PRIMARY KEY AUTOINCREMENT, totCost FLOAT, amountGiven INTEGER, change INTEGER)')
db.commit()
cursor.execute('CREATE TABLE sale (saleId INTEGER PRIMARY KEY AUTOINCREMENT, transactionId INTEGER, prodId INTEGER, price INTEGER, quantity INTEGER, refund INTEGER, mealDeal INT, halfCookie INT, FOREIGN KEY (prodId) REFERENCES products(pos), FOREIGN KEY (transactionId) REFERENCES transactions(transactionId));')
db.commit()
cursor.execute('CREATE TABLE cur_transaction (prodId INTEGER, price INTEGER, quantity INTEGER, FOREIGN KEY (prodId) REFERENCES products(pos))')
db.commit()

