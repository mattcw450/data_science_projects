#!/usr/bin/env python
"""
Very simple HTTP server in python.
Usage::
    ./dummy-web-server.py [<port>]
Send a GET request::
    curl http://localhost
Send a HEAD request::
    curl -I http://localhost
Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost
"""
from http.server import BaseHTTPRequestHandler,HTTPServer
#import socketserver

import base64
import sqlite3
import numpy as np


###################################  1  #######################################
# Create a database
db = sqlite3.connect('products.db')

# Get a cursor object
cursor = db.cursor()


###################################  2  #######################################
def build_action_refill(where,what):
    text = "<action>\n"
    text += "<type>refill</type>\n"
    text += "<where>"+where+"</where>\n"
    text += "<what>"+base64.b64encode(what.encode()).decode("ascii")+"</what>\n"      # Needed to be encoded to work from python 2 to python 3 (this works - don't change it)
    text += "</action>\n"
    return text

def build_action_append(where,what):
    text = "<action>\n"
    text += "<type>append</type>\n"
    text += "<where>"+where+"</where>\n"
    text += "<what>"+base64.b64encode(what.encode()).decode("ascii")+"</what>\n"      # Needed to be encoded to work from python 2 to python 3 (this works - don't change it)
    text += "</action>\n"
    return text

def build_action_total(value):
    text = "<action>\n"
    text += "<type>total</type>\n"
    text += "<value>"+str(value)+"</value>\n"              # This needed to be a string
    text += "</action>\n"
    return text

def build_action_reset():
    text = "<action>\n"
    text += "<type>reset</type>\n"
    text += "</action>\n"
    return text



###################################  3  #######################################
"""
We need a way to identify if we're in a transaction or not and what our 
transaction number is.

Will set in_transaction to False initially and the transaction number to be 
infinity just so it will throw an error if this doesn't get changed.

title will be the title so when you click on sandwiches and drinks this will change
"""
in_transaction = False
tran_numb = np.inf
target_display = str()
title = str()


###################################  4  #######################################
def check_make_transaction(in_transaction, tran_numb):
    """
    A function that checks whether the server is in the middle of a transaction or not.
    If not, a new transaction is created and the transaction status is changed
    """
    # Want to know the transaction status
    if in_transaction == False:
        # Want to make a new transaction
        cursor.execute("INSERT INTO transactions VALUES (NULL, NULL, NULL, NULL);")
        db.commit()    
        in_transaction = True
        
    # in_transaction should now be True        
    if in_transaction == True:
        # Find the transaction number...
        cursor.execute("SELECT transactionId FROM transactions ORDER BY transactionId DESC LIMIT 1;")
        tran_numb = cursor.fetchall()[0][0]
        return in_transaction, tran_numb
        




#def act_plu(dic, subtex, tot):
def act_plu(dic, additSubtext):
    """
    Looks up the input PLU code and adds that item to the sale table  IF THAT ITEM EXISTS 
    """
    global in_transaction
    global tran_numb
    global target_display
    # Check to see if it's a valid PLU code...
    cursor.execute("SELECT * FROM products WHERE plu = {}".format(dic['plu']))
    isItem = cursor.fetchall()
    if len(isItem) == 0:      # Not valid
        additSubtext = "This is not a valid PLU code"
        return additSubtext
    elif len(isItem) != 0:    # Is valid
        # Check whether in a transaction or not...
        in_transaction, tran_numb = check_make_transaction(in_transaction, tran_numb)
        quantity = int(dic['num'])
        # now need to add the product to the sale table
        cursor.execute("SELECT pos, price, name FROM products WHERE plu = {}".format(dic['plu']))
        query = cursor.fetchall()[0]
        if dic['refund']==str(0):
            price = query[1]
        elif dic['refund']==str(4):
            price = query[1] * -1  
            quantity = quantity *-1
        prod_numb = query[0]
        name = query[2]     # not needed anymore but optional if ever needs to be modified
        print(tran_numb, type(tran_numb), prod_numb, type(prod_numb), price, type(price), quantity, type(quantity), dic['refund'], type(dic['refund']))
        cursor.execute("INSERT INTO sale (transactionId, prodId, price, quantity, refund) VALUES ({}, {}, {}, {}, {})".format(tran_numb, prod_numb, price, quantity, dic['refund']))
        db.commit()
        return additSubtext
            
            

def act_cash(dic, subtex):
    """
    Deals with the response when action = cash
    
    It closes the transaction and tells the right amount of change to give
    """
    global in_transaction
    global tran_numb
    global target_display
    global subtext   
    # Need to know the total of the current transaction...
    cursor.execute("SELECT SUM(price*ABS(quantity)) FROM sale WHERE transactionId = {} GROUP BY transactionId".format(tran_numb))
    cur_trans_tot = cursor.fetchall()[0][0]
    print('cur_trans_tot[0][0] = ', cur_trans_tot)
    if float(dic['cash']) == float(cur_trans_tot):
        # They paid the correct amount
        cursor.execute("UPDATE transactions SET totCost={}, amountGiven={}, change={} WHERE transactionId={}".format(cur_trans_tot, float(dic['cash']), 0, tran_numb))
        in_transaction = False
        subtex = "Transaction Completed"
        target_display = str()
        db.commit()
        return subtex
    elif float(dic['cash']) > float(cur_trans_tot):
        # They paid more and need change...
        cursor.execute("UPDATE transactions SET totCost={}, amountGiven={}, change={} WHERE transactionId={}".format(cur_trans_tot, float(dic['cash']), float(dic['cash']) - float(cur_trans_tot), tran_numb))
        in_transaction = False
        subtex = "Change needed is &#163;{}".format((float(dic['cash'])-(float(cur_trans_tot)))/100)
        target_display = str()
        db.commit()
        return subtex



#def act_prog(dic, subtex, tot):
def act_prog(dic, additSubtext):
    """
    Looks up the pos and shift number to correctly identify the item pressed
    and adds this item to the sale table IF THE ITEM EXISTS IN THE DATABASE
    
    a few items in the database have a typo either deliberately or accidently
    ("Panini Bacon, Brie, Cranberry" and the "Panini Mushroom Melt") where the 
    shift and classid are round the wrong way. I kept this as it was in case 
    this was what the spec meant by "if it exists". Can easily fix the database 
    though for future reference
    """
    global in_transaction
    global tran_numb
    global target_display
    global subtext
    # TRANSACTION CHECK...
    in_transaction, tran_numb = check_make_transaction(in_transaction, tran_numb)
    # Find the item in the products table...
    if int(dic['shift'])==0:
        # Can match any entry in the table with shift 0 or negative shift
        quantity = int(dic['num'])
        cursor.execute("SELECT productid, price, name FROM products WHERE pos = {} AND shift <= {};".format(dic['pos'], dic['shift']))
        try:
            query = cursor.fetchall()[0]
        except IndexError:
            additSubtext = "This item wasn't in the database"
        else:
            prod_numb = query[0]
            if dic['refund']==str(0):
                price = query[1]
            elif dic['refund']==str(4):
                price = query[1] * -1
                quantity = quantity*-1
            name = query[2]           # can be deleted as not used 
            cursor.execute("INSERT INTO sale (transactionId, prodId, price, quantity, refund) VALUES ({}, {}, {}, {}, {})".format(tran_numb, prod_numb, price, quantity, dic['refund']))
            db.commit()
    elif int(dic['shift']) != 0:
        # Can match any entry in the table with matching shift or matching negative shift
        quantity = int(dic['num'])
        cursor.execute("SELECT productid, price, name FROM products WHERE pos = {} AND ABS(shift) = {}".format(dic['pos'], dic['shift']))
        try:
            query = cursor.fetchall()[0]
        except IndexError:
            additSubtext = "This item wasn't in the database"
        else:
            prod_numb = query[0]
            if dic['refund']==str(0):
                price = query[1]
            elif dic['refund']==str(4):
                price = query[1] * -1
                quantity = quantity * -1
            name = query[2]      # can be deleted as not used
            cursor.execute("INSERT INTO sale (transactionId, prodId, price, quantity, refund) VALUES ({}, {}, {}, {}, {})".format(tran_numb, prod_numb, price, quantity, dic['refund']))
            db.commit()
    return additSubtext

def act_clr(dic, additSubtex):
    """
    Voids the current transaction if in a transaction. 
    Else, displayes an error message
    """
    global in_transaction
    global tran_numb
    global target_display
    global subtext
    if in_transaction == True:       # we want to void the whole transaction and delete it from our database
        cursor.execute("DELETE FROM sale WHERE transactionId = {}".format(tran_numb))
        db.commit()
        cursor.execute("DELETE FROM transactions WHERE transactionId = {}".format(int(tran_numb)))
        db.commit()
        in_transaction = False
        target_display = str()
        additSubtex = "The Transaction Has Been Void"
        return additSubtex
    elif in_transaction == False:
        additSubtex = "There is No Transaction Active"
        return additSubtex


def act_status(dic, tit, subtex):
    """
    When the action is status, we change the page to sandwiches/paninis or to 
    drinks and snacks. SNAAAAAAAAAAAACKS https://www.youtube.com/watch?v=L52dVwMJTEc
    
    This will change the title to the relevant page name    
    """
    global target_display
    global subtext
    global title
    if int(dic['page'])==1:
        tit = str("Drinks and Snacks")
        subtex = "<br>" + str(target_display)
        return tit, subtex
    elif int(dic['page'])==2:
        tit = str("Sandwiches")
        subtex = "<br>" + str(target_display)
        return tit, subtex


###################################  5  #######################################
    
class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type'.encode(), 'text/html')
        self.end_headers()

    """
    Okay so initially, my competence in object oriented programming was lacking 
    slightly. So when I first started this tills coursework, I made many 
    functions outside the class "S" and made variables global. I realise now this
    wasn't a great way to do this and have become a lot more able when it comes
    to OOP. I do not have the time to re-do this using methods and self instead 
    so since it is working, I will leave it like as it is. In terms of efficiency 
    and accuracy, everything still works fine.
    """    
    global in_transaction
    global tran_numb
    global title

    
    def do_GET(self):
        global in_transaction
        global tran_numb
        global title
        title = str()
        additSubtext = None
        parts = self.path.split("?",1);        

        if (self.path == '/'):
            self.send_response(200)
            fname = 'till.html';
            file = open(fname,"r")
            text = file.read()
            self.send_header('Content-type'.encode(), 'text/html')
        elif (self.path == '/till.css'):
            self.send_response(200)
            fname = 'till.css';
            file = open(fname,"r")
            text = file.read()
            self.send_header('Content-type'.encode(), 'text/css')
        elif (self.path == '/till2.html'):
            self.send_response(200)
            fname = 'till2.html';
            file = open(fname,"r")
            text = file.read()
            self.send_header('Content-type'.encode(), 'text/html')
        elif (self.path == '/till.js'):
            self.send_response(200)
            fname = 'till.js';
            file = open(fname,"r")
            text = file.read()
            self.send_header('Content-type'.encode(), 'application/javascript')
        elif (parts[0] == '/action'):
            self.send_response(200)

            subtext = "";
########################################################################################################           
            

            # I will make a dictionary that stores all the information sent by the front end of the server. This will be the main reference point for this backend
            dictionary = {}
            for p in parts[1].split("&"):      # the request has action/ followed by a=b & c=d & e=f...
                q, v = p.split("=")
                dictionary[q] = v
                subtext = ""

            total = 0
            subtext = str()

            """
            This next part simply calles the functions we made earlier at the 
            relevant points.
            """
            if dictionary['action']=='plu':
                additSubtext = act_plu(dictionary, additSubtext)

            if dictionary['action']=='cash':
                sub = act_cash(dictionary, subtext)
                subtext += sub
            
            if dictionary['action']=='program':
                additSubtext = act_prog(dictionary, additSubtext)
                if additSubtext is not None:
                    subtext = additSubtext
                
            if dictionary['action']=='clr':
                additSubtext = act_clr(dictionary, subtext)
                subtext += additSubtext
                    
            if dictionary['action']=='status':
                title, subtext = act_status(dictionary, title, subtext)
            
            
            
            
            
###################################  6  #######################################

            # Fill in the current transaction table
            if tran_numb != np.inf:
                # Delete everything in the current transaction so we can recalculate refunds and deals
                cursor.execute("DELETE FROM cur_transaction")
                db.commit()
                cursor.execute("INSERT INTO cur_transaction SELECT prodId, SUM(price * ABS(quantity)), SUM(quantity) FROM sale WHERE transactionId = {} GROUP BY prodId".format(tran_numb))
                db.commit()


            
            
###################################  7  #######################################
            
            
            ###################################################################
            ######################## CALCULATE OFFERS #########################
            ###################################################################
            """
            Need to know the upper bound (UB) on the number of offers that can 
            be added. First, it will be the number of cookies/shortbread in 
            that transaction. This UB will be lowered if there are less drinks
            than cookies/shortbread. Then we will need to calculate the number 
            of hot and cold drinks. Cold drinks will always get pririty in a 
            meal deal over hot drinks. Will then need the number of paninis and 
            sandwhiches in the order to see how many free cookies will be given.
            
            Priorities are:
                1. Cold drinks & panini/sandwich
                2. Hot drinks & panini/sandwich
                3. Hot drinks
                
            1 Gives free cookies, 2 gives free cookies, 3 gives half price 
            cookies
            """
            
            """
            Number of sandwhiches/paninis is the upper bound (UB) for the 
            number of meal deals. This can then be lowered by the number of 
            drinks. UB can be lowered further by the number of cookies/cr
            """
            if dictionary['action']=='program' or dictionary['action']=='plu':
                # delete old meal deals only if in same transaction
                cursor.execute("SELECT * FROM sale WHERE transactionId = {} AND (mealDeal = 1 OR halfCookie = 1)".format(tran_numb))
                try:
                    current_deals = cursor.fetchall()[0]
                except IndexError:
                    pass
#                    print("No deals to delete")
                    # No deals to delete                    
                else:
                    # There were deals that now need to be deleted and recalculated
                    # Delete all previously calculated meal deal discounts...
                    cursor.execute("DELETE FROM sale WHERE mealDeal = 1 AND transactionId = {}".format(tran_numb))
                    cursor.execute("DELETE FROM sale WHERE halfCookie = 1 AND transactionId = {}".format(tran_numb))
                    db.commit()             


                
                # Set an upper bound on the number of meal deals and half cookies...
                MD_UB = 0         # Initially we assume this is 0
                C_UB = 0
  
                # Number of crisps, popcorn or fruit 
                cursor.execute("SELECT SUM(cur_transaction.quantity) FROM cur_transaction JOIN products ON cur_transaction.prodId = products.productid WHERE cur_transaction.quantity > 0 AND (products.classid = 11 OR products.classid = 8 OR products.classid = 10);")
                MD_num_snack = cursor.fetchall()[0][0]
                
                # Number of paninis or sandwhiches
                cursor.execute("SELECT SUM(cur_transaction.quantity) FROM cur_transaction JOIN products ON cur_transaction.prodId = products.productid WHERE cur_transaction.quantity > 0 AND (products.classid = 7 OR products.classid = 5);")
                MD_num_main = cursor.fetchall()[0][0]
                
                # Number of drinks
                cursor.execute("SELECT SUM(cur_transaction.quantity) FROM cur_transaction JOIN products ON cur_transaction.prodId = products.productid WHERE cur_transaction.quantity > 0 AND (products.classid = 1 OR products.classid = 2 OR products.classid = 3 OR products.classid = 4);")
                MD_num_drink = cursor.fetchall()[0][0]
                                
                # Number of hot drinks
                cursor.execute("SELECT SUM(cur_transaction.quantity) FROM cur_transaction JOIN products ON cur_transaction.prodId = products.productid WHERE cur_transaction.quantity > 0 AND (products.classid = 1 OR products.classid = 2 OR products.classid = 3);")
                MD_num_drink_hot = cursor.fetchall()[0][0]
                
                # Number of cookies/shortbread
                cursor.execute("SELECT SUM(cur_transaction.quantity) FROM cur_transaction JOIN products ON cur_transaction.prodId = products.productid WHERE cur_transaction.quantity > 0 AND (products.classid = 9);")
                C_num_cook = cursor.fetchall()[0][0]

                
                
                if MD_num_drink and MD_num_snack and MD_num_main:   # If there is at least one of each item in the meal deal...
                    # Update the upper bound...
                    """
                    The upper bound for the number of meal deals we can have will be the minimum 
                    between the number of snacks, mains (sandwich/panini) and drinks. 
                    
                    E.g. 4 snacks, 3 paninis/sandwiches , and 6 drinks      would have a maximum of 3 meal deals (UB = 3)
                    """
                    MD_UB = min(MD_num_snack, MD_num_main, MD_num_drink)    # this will be at least 1
                    # Now need to apply the meal deal discounts
                    """
                    This part is now scaleable.
                    
                    - The snacks are and can be different prices. 
                    - The meal deal should give the maximum discounts where possible.
                    So when we have an option of prices to choose from, we will choose the largest

                    snack_prices is a list of tuples with prices for all snacks and quantities.
                        e.g. [(65, 4), (85, 5)] Which says 4 items for 65p each, 5 items for 85p
                        
                    We then order this list to become:
                        pricesMD = [85, 85, 85, 85, 85, 65, 65, 65, 65]
                        
                    Then we put an upper bound on it.. e.g. can give 6 meal deals...
                    
                    meal_deal_discounts = [85, 85, 85, 85, 85, 65]
                    
                    And then we add each meal deal discount to the sale table.
                    """
                    cursor.execute("SELECT cur_transaction.price/cur_transaction.quantity, cur_transaction.quantity FROM cur_transaction JOIN products ON cur_transaction.prodId = products.productid WHERE cur_transaction.quantity > 0 AND (products.classid = 11 OR products.classid = 8 OR products.classid = 10) ORDER BY cur_transaction.price/cur_transaction.quantity DESC;")
                    snack_prices = cursor.fetchall()
                    pricesMD = []
                    for i in range(len(snack_prices)):
                        for j in range(snack_prices[i][1]):
                            pricesMD.append(snack_prices[i][0])
                    meal_deal_discounts = pricesMD[0:MD_UB]
                    
                    for i in range(len(meal_deal_discounts)):
                        cursor.execute("INSERT INTO sale (transactionId, prodId, price, quantity, mealDeal, refund) VALUES ({}, {}, {}, {}, {}, {});".format(tran_numb, 5001, meal_deal_discounts[i]*-1, 1, 1, 0))
                        db.commit()
                   
                 
                    
                    
                """   
                Since the meal deal is always a better deal than the half price cookie, 
                we calculate the cookie deals second using the remaining hot drinks from 
                meal deals.
                """
                if MD_num_drink_hot and C_num_cook:       # IF they have ordered hot drinks and cookies
                    # Cookie upper bound...
                    """
                    The cookie deal upper bound requires a little more thinking.
                    
                    The amount of cookie deals we can give can't be more than:
                        1. The number of hot drinks in the order
                        2. The number of cookies in the order
                        3. The number of REMAINING hot drinks after we MAY have used some in the meal deals
                        
                    Point number 3 needs a little more explaining. If we had an order of:
                        10 hot drinks
                        4 cold drinks
                        6 paninis
                        5 packets of crisps
                        12 cookies
                        
                        We would use all of the cold drinks and 1 hot drink to get 5 meal deals.
                        this would leave us with 9 hot drinks, and 12 cookies. So we get 9 cookie deals.
                        
                        This 9 is simply:
                            = (number of drinks ordered) - (the number of meal deals given)
                            =        (10 + 4)            -              (5)
                            =    9
                            
                    So we choose an upper bound by the min of:
                        1. The number of hot drinks in the order
                        2. The number of cookies in the order
                        3. The number of drinks - the number of meal deals 
                    """
                    C_UB = min((MD_num_drink-MD_UB), MD_num_drink_hot, C_num_cook)
                    
                    # Now need to apply all the half cookie deals
                    # First need to ensure that the customer will always receive the maximum discount (e.g. if they were allowed one free cookie and chose two, one being 80p and the other being 60p, they would get the 80p cookie half price and pay £1 as opposed to 30p + 80p = £1.10)
                    """
                    Similar to before, this part is future proof so if we added a more expensive cookie,
                    The deal will apply to this before less expensive ones.
                    
                    
                    
                    - The cookies could be different prices. 
                    - The cookie deal should give the maximum discounts where possible.
                    So when we have an option of prices to choose from, we will choose the largest

                    cookie_prices is a list of tuples with prices for all cookies and quantities.
                        e.g. [(65, 4), (85, 5)] Which says 4 items for 65p each, 5 items for 85p
                        
                    We then order this list to become:
                        pricesC = [85, 85, 85, 85, 85, 65, 65, 65, 65]
                        
                    Then we put an upper bound on it.. e.g. can give 6 cookie deals...
                    
                    half_cookie_discounts = [85, 85, 85, 85, 85, 65]
                    
                    And then we add each cookie deal discount to the sale table making sure that we take half the price of the cookie off.
                    """
                    cursor.execute("SELECT cur_transaction.price/cur_transaction.quantity, cur_transaction.quantity FROM cur_transaction JOIN products ON cur_transaction.prodId = products.productid WHERE cur_transaction.quantity > 0 AND products.classid = 9 ORDER BY cur_transaction.price/cur_transaction.quantity DESC;")
                    cookie_prices = cursor.fetchall()
                    pricesC =  []
                    for i in range(len(cookie_prices)):
                        for j in range(cookie_prices[i][1]):
                            pricesC.append(cookie_prices[i][0])
                    half_cookie_discounts = pricesC[0:C_UB]
                    for i in range(len(half_cookie_discounts)):
                        """
                        Note that in the insert statement, we add a value of -0.0001 
                        this is so that the floating point error is ommitigated when rounding. 
                        This ensures .5 always rounds up
                        """
                        cursor.execute("INSERT INTO sale (transactionId, prodId, price, quantity, halfCookie, refund) VALUES ({}, {}, {}, {}, {}, {});".format(tran_numb, 5002, round(half_cookie_discounts[i]*-0.5-0.0001), 1, 1, 0))    # the - 0.0001 is due to floating point error when rounding, this ensures .5 always rounds up
                        db.commit()
                
                
                

                
###################################  8  #######################################            
                """
                Now make the target display show the right thing            
                """
                cursor.execute("SELECT sale.quantity, products.name, sale.price*ABS(sale.quantity), sale.refund FROM sale JOIN products ON products.productid = sale.prodId WHERE sale.transactionId = {}".format(tran_numb))
                target_display_new = cursor.fetchall()
                cursor.execute("SELECT SUM(ABS(quantity)*price) FROM sale WHERE transactionId = {}".format(tran_numb))
                total = cursor.fetchone()[0]
                """
                The next part adds the new item as a string with its price and quantity
                to the display so the cashier can see what items have been added.
                """
                for line in range(len(target_display_new)):
                    if target_display_new[line][3] == 0:
                        subtext += str(target_display_new[line][0]) + 'X ' + str(target_display_new[line][1]) + "    " + "&pound;" + str(target_display_new[line][2]/100) + "<br>"
                    elif target_display_new[line][3] == 4:
                        subtext += str(target_display_new[line][0]) + 'X ' + str(target_display_new[line][1]) + "    " + "&pound;" + str(target_display_new[line][2]/100) + "(Refund)" + "<br>"
                    else:
                        subtext = "This did not work"    # Should never reach this point but good for error checking
            
         
######################################################################################## 
            text  = '<?xml version="1.0" encoding="UTF-8"?>\n'
            text += "<response>\n"
            text += build_action_total(total);
            text += build_action_refill("target", subtext + "<br>" + "Total is :" + "&pound;" + str(total/100));
            text += build_action_refill("title", str(title));    # give change   "Change &pound;0.00"
            text += build_action_reset();
            text += "</response>\n"
            self.send_header('Content-type'.encode(), 'application/xml')
        else:
            self.send_response(404)
            fname = '404.html';
            file = open(fname,"r")
            text = file.read()
            self.send_header('Content-type'.encode(), 'text/html')
            
        self.end_headers()
        self.wfile.write(text.encode())

    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        self._set_headers()
        self.wfile.write("<html><body><h1>POST!</h1></body></html>")
        
def run(server_class=HTTPServer, handler_class=S, port=8090):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()

