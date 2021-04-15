# -*- coding: utf-8 -*-
"""
Software Technologies for Data Science

Lab 8 - Mini Project

Task 2.1

@author: Matthew
"""

import pandas as pd
import numpy as np
import sqlite3


# Create a database
db = sqlite3.connect('products.db')

# Get a cursor object
cursor = db.cursor()

"""
1.  A daily sales report that shows how much of each product has been sold, and the 
    total value of sales. It should also show the total cash, debit and card payments 
    taken. It should also lists all discounts given, both the number and value.
"""

# How much of each product has been sold
cursor.execute("SELECT products.name, products.productid, SUM(sale.quantity) FROM sale JOIN products ON sale.prodId = products.productid GROUP BY sale.prodId;")
quants = cursor.fetchall()
quants = pd.DataFrame(quants, columns=['Item Name', 'Product ID', 'Number Sold'])

export_quants = quants.to_csv("QuantitiesSold.csv") #Don't forget to add '.csv' at the end of the path


# The total value of all sales
cursor.execute("SELECT SUM(totCost) FROM transactions")
totals = cursor.fetchall()
totals = pd.DataFrame(totals, columns=['Total Value of all Sales (in pence)'])

export_totals = totals.to_csv("TotalValueOfSales.csv")


# The total deals 
cursor.execute("SELECT products.name, COUNT(sale.mealDeal), SUM(sale.price) FROM sale JOIN products ON sale.prodId = products.productid WHERE mealDeal = 1")
Mdeal = cursor.fetchall()
cursor.execute("SELECT products.name, COUNT(sale.halfCookie), SUM(sale.price) FROM sale JOIN products ON sale.prodId = products.productid WHERE halfCookie = 1")
Cdeal = cursor.fetchall()

Mdeal = pd.DataFrame(Mdeal, columns=["Type of Deal", "Total Number of Deals", "Total Deals Cost (pence)"])
Cdeal = pd.DataFrame(Cdeal, columns=["Type of Deal", "Total Number of Deals", "Total Deals Cost (pence)"])
deals = [Mdeal, Cdeal]
deals = pd.concat(deals)

export_deals = deals.to_csv("TotalNumberOfDeals.csv")


###############################################################################
###### Due to how I have written my code, there is no ability to find #########
###### which payment type was used in each sale or distinguish between days ###
###############################################################################

"""
2.  A product report that, for a given product shows the total volume and 
    value of sales for a product on each day during the reporting period. 
"""

# Again my code doesn't use dates anywhre so this bit cant be done
# But if I were to write the sql query, it would be something like:
""" SELECT SUM(quantity) AS 'Total_Volume', 
           SUM(price) AS 'Value_of_Sales',
           day
    FROM sale
    WHERE prodId = 'certain items product id'
    GROUP BY day ASC;
"""
# Then I would do a cursor.fetchall()
# And similar to before, export to a csv


###############################################################################
"""
3.  Export all of the item data including the transaction to which it belong to 
    a csv file for use in Task 2.2 
"""
"""
Need to make a csv like in 2.2 
has:
    itemId
    timestamp (not needed - good because I dont have it)
    transaction
    productId

itemId is basically our saleId
transaction is our transactionId
productId is the same as our productId
"""

cursor.execute("SELECT saleId, transactionId, prodId FROM sale;")
task2_2Table = cursor.fetchall()
task2_2Table = pd.DataFrame(task2_2Table, columns=["itemid", "transactionid", "productid"])
export_task2Table = task2_2Table.to_csv("Task2_2Table.csv")



# Can also get the Sale Table
cursor.execute("SELECT * FROM sale;")
sale_table = cursor.fetchall()
sale_names = ["saleId", "transactionId", "prodId", "price", "quantity", "refund", "mealDeal", "halfCookie"]

sale_df = pd.DataFrame(sale_table, columns=sale_names)

export_sale = sale_df.to_csv("saleTable.csv")


# And the Transaction Table
cursor.execute("SELECT * FROM transactions;")
transaction_table = cursor.fetchall()
transaction_names = ["transactionId", "totCost", "amountGiven", "change"]

transaction_df = pd.DataFrame(transaction_table, columns=transaction_names)

export_transactions = transaction_df.to_csv("transactionTable.csv")







