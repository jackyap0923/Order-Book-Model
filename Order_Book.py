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
        self.bids = sorted(self.bids.keys(), reverse=True)
        self.asks = sorted(self.asks.keys())

    def add_limit_order(self, side, price, quantity):
        order_id = next(self.order_id_counter)
        order = Order(order_id, side, price, quantity)
        book = self.bids if side == 'bid' else self.asks
        book[price].append(order)

        self.update_book() #Rearrages the book after adding a new order

        return order
    
    def add_market_order(self, side, quantity):
        book = self.bids if side == 'bid' else self.asks
        if not book:
            raise ValueError("No orders available in market.")
        
