import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, deque
import warnings
import itertools
warnings.filterwarnings("ignore")

#Order Book Module
class Order:
    def __init__(self, order_id, side, price, quantity):
        if price <= 0:
            raise ValueError("Price must be greater than 0")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        if side not in ['bid', 'ask']:
            raise ValueError("Side must be 'bid' or 'ask'")
        
        self.order_id = order_id
        self.side = side # 'bid' or 'ask'
        self.price = price
        self.quantity = quantity
    
    def __repr__(self):
        return f"Order(order_id={self.order_id}, side={self.side}, price={self.price}, quantity={self.quantity})"

class OrderBook:
    def __init__(self):
        #Entire Order Book stored in dictionaries with deques for fast access
        self.bids = defaultdict(deque)
        self.asks = defaultdict(deque)
        self.order_id_counter = itertools.count()

    def update_book(self):
        """"Update the order book by sorting bids and asks."""
        self.bids = sorted(self.bids.keys())
        self.asks = sorted(self.asks.keys(),revserse=True)

    def order_fill_logic(self, orders, quantity):
        for order in orders:
            if order.quantity >= quantity: #order can be fully filled
                order.quantity -= quantity 
                if order.quantity > 0:
                    break #Order remains in book but with reduced quantity and exit for
                elif order.quantity == 0:
                    orders.popleft() #Remove order if quantity is zero and exit for
                    break
                else:
                    raise ValueError("Order quantity cannot be negative.")
                    
            else: #Order is partially filled
                quantity -= order.quantity 
                orders.popleft() 
            
        return quantity #Return remaining quantity to be filled
    
    def liquidity_check(self, book, order):
        matching_prices = []
        price_level = order.price
        quantity = order.quantity
        side = order.side        
        total_quantity = 0

        #Checking for all available liquidity at or below price
        for price in book.keys():
            if (side == 'bid' and price <= price_level) or (side == 'ask' and price >= price_level):
                matching_prices.append(price)
                orders = book[price]
                for o in orders:
                    total_quantity += o.quantity
                    if total_quantity >= quantity:
                        return matching_prices, total_quantity
                    
            else:
                break #Exit if price is not within the limit

        return matching_prices, total_quantity

    def add_order(self, book, order):
        """"Add an order to the order book. Does not change order id."""
        price = order.price
        book[price].append(order) 

    def limit_order(self, side, price, quantity):
        order_id = next(self.order_id_counter)
        limit_order = Order(order_id, side, price, quantity)
        matching_book = self.bids if side == 'ask' else self.asks #Looks at opposite side of book to check for matching orders
        book = self.bids if side == 'bid' else self.asks #

        #Check if order can be filled or partially filled
        matching_prices, total_quantity = self.liquidity_check(matching_book, limit_order)
        
        #If no matching prices, add to book and print 
        if not matching_prices:
            self.add_order(book, limit_order)
            print(f"No orders available at or below price {price}.")
        else:
            for match_price in matching_prices:
                orders = matching_book[match_price]
                limit_order.quantity = self.order_fill_logic(orders, limit_order.quantity)

                if limit_order.quantity == 0: #Order fully filled
                    return print(f"Order {order_id} fully filled at price {match_price}.")

            if limit_order.quantity > 0: #Order partially filled
                self.add_order(book, limit_order) #Add remaining order to book
                print(f"Order {order_id} partially filled. Remaining quantity: {limit_order.quantity}. Added to book at price {price}.")

        self.update_book() #Rearranges the book after processing limit order

        return limit_order
    
    def market_order(self, side, quantity):
        book = self.bids if side == 'ask' else self.asks #Look at opposite side of book e.g. people buying will look at asks, vice versa.
        if not book:
            raise ValueError("No orders available in market.")
        else:
            if side =='bid': # Look at ask book
                best_price = min(book.keys())
            elif side =='ask': # Looks at bid book
                best_price = max(book.keys())
            else:
                raise ValueError("Side must be 'bid' or 'ask'")
            
            orders = book[best_price]

            self.order_fill_logic(orders, quantity) #Fill the market order with available orders at market price

            if not orders: # If no orders left at this price, remove the price level from the book
                del book[best_price]

        self.update_book() #Rearranges the book after processing market order

        #Order must be filled immeidiately or cancelled. Filled until all improvement prices are filled.
        def fill_or_kill_order(self, side, price, quantity, limit=False): 
            book = self.bids if side =='ask' else self.asks
            
            if not book:
                raise ValueError("No order avaialable in market.")
            if price < book.keys():
                raise ValueError(f"No orders available at or below price {price}.")
            
            fok_prices, 
            
            #Raise error if not enough liquidity is present
            if total_quantity < quantity:
                raise ValueError(f"Not enough quantity available at or below price {price}.")
            else:
                for price in fok_prices:
                    orders = book[price]
                    self.order_fill_logic(orders, quantity)
                    if not orders:
                        del book[price]
