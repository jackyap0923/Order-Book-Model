import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sortedcontainers import SortedDict
from collections import deque
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

class StopOrder:
    def __init__(self, stop_order_id, side, stop_price, quantity):
        if stop_price <= 0:
            raise ValueError("Stop price must be greater than 0")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        if side not in ['bid', 'ask']:
            raise ValueError("Side must be 'bid' or 'ask'")
        
        self.stop_order_id = stop_order_id #separate from order_id
        self.side = side #bid or ask
        self.stop_price = stop_price
        self.quantity = quantity

    def __repr__(self):
        return f"StopOrder(stop_order_id={self.stop_order_id}, side={self.side}, stop_price={self.stop_price}, quantity={self.quantity})"

class OrderBook:
    def __init__(self):
        #Entire Order Book stored in dictionaries with deques for fast access
        self.bids = SortedDict(lambda x: -x)  
        self.asks = SortedDict()
        self.order_id_counter = itertools.count()
        self.stop_market_orders_bid =SortedDict(lambda x: -x) #For bid stop market orders, key is stop price, value is a list of orders
        self.stop_market_orders_ask = SortedDict() #For bid stop market orders, key is stop price, value is a list of orders
        self.stop_limit_orders_bid = SortedDict(lambda x: -x) #For bid stop limit orders, key is stop price, value is a list of orders
        self.stop_limit_orders_ask = SortedDict() #For ask stop limit orders, key is stop price, value is a list of orders
        self.stop_order_id_counter = itertools.count() #Separate counter for stop orders

    def get_best_bid(self):
        best_bid = self.bids.peekitem(0)[0] if self.bids else None
        return -best_bid
    
    def get_best_ask(self):
        best_ask = self.asks.peekitem(0)[0] if self.asks else None
        return best_ask

    def order_fill_logic(self, side, orders, quantity):
        while quantity > 0 and orders:
            order = orders[0]

            if order.quantity > quantity: #order can be fully filled
                order.quantity -= quantity 
                print(f"[Taker] Order Filled at price {order.price}") #Order remains in book but with reduced quantity and exit for
                return print(f"[Maker] Order_id: {order.order_id}. {order.quantity} partially filled at price {order.price}. Remaining quantity: {order.quantity}")
                
            elif order.quantity == quantity:
                orders.popleft() #Remove order from book if maker order is fully filled
                print(f"[Taker] Order Filled at price {order.price}")
                return  print(f'[Maker] Order_id: {order.order_id}. {order.quantity} fully filled at price {order.price}.')
                
            else: #order.quantity < quantity
                quantity -= order.quantity
                print(f"[Maker] Order_id: {order.order_id}. {order.quantity} fully filled at price {order.price}.")
                print(f"[Taker] Partially filled at price {order.price}. Remaining quantity: {quantity}.")
                orders.popleft()
                    
        if quantity > 0:
            print(f"[Taker] Unfilled quantity: {quantity} due to lack of liquidity.")
            return quantity
        
    
    def liquidity_check(self, book, order):
        matching_prices = []
        price_level = order.price
        quantity = order.quantity
        side = order.side        
        total_quantity = 0

        #Checking for all available liquidity at or below price
        for price in book:
            if (side == 'bid' and price <= price_level) or (side == 'ask' and -price >= price_level):
                matching_prices.append(price)
                orders = book[price]
                for o in orders:
                    total_quantity += o.quantity
                    if total_quantity >= quantity:
                        return matching_prices, total_quantity
                    
            else:
                break #Exit if price is not within the limit

        return matching_prices, total_quantity

    def stop_market_order_check(self):
        best_bid = -self.get_best_bid()
        best_ask = self.get_best_ask()
        # Check if there are any stop market orders that can be triggered
        if best_bid is not None and self.stop_market_orders_bid:
            for stop_price, orders in self.stop_market_orders_bid.items():
                #Start clearing orders at best_bid until it is above stop_price
                if stop_price >= best_bid:
                    for o in orders:
                        
        return None

    def add_order(self, book, order):
        """"Add an order to the order book. Does not change order id."""
        price = order.price
        if order.price not in book:
            book[price] = deque()
        
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
            return print(f"Order {order_id} added to book at price {price}.")
        
        for match_price in matching_prices:
            orders = matching_book[match_price]
            limit_order.quantity = self.order_fill_logic(orders, limit_order.quantity)

            if not orders: #If no orders left at this price, remove the price level from the book
                del matching_book[match_price]

            if limit_order.quantity == 0: #Order fully filled
                return print(f"Order {order_id} fully filled at price {match_price}.")

        if limit_order.quantity > 0: #Order partially filled
            self.add_order(book, limit_order) #Add remaining order to book
            print(f"Order {order_id} partially filled. Remaining quantity: {limit_order.quantity}. Added to book at price {price}.")

        return limit_order
    
    def market_order(self, side, quantity):
        order_id = next(self.order_id_counter)
        market_order = Order(order_id, side, None, quantity) #Price is None for market orders
        matching_book = self.bids if side == 'ask' else self.asks #Look at opposite side of book e.g. people buying will look at asks, vice versa.
        
        if not matching_book:
            raise ValueError("No orders available in market.")
        
        best_price = self.get_best_ask() if side == 'bid' else self.get_best_bid()  #Get the best price available
            
        orders = matching_book[best_price]

        remaining_quantity = self.order_fill_logic(orders, quantity) #Fill the market order with available orders at market price
        
        market_order.quantity = quantity - remaining_quantity #Update market order to filled quantity
        market_order.price = best_price #Set market order price to the best price available

        if not orders: # If no orders left at this price, remove the price level from the book
            del matching_book[best_price]

        return market_order
    
    def fill_or_kill_order(self, side, price, quantity):
        """Order must be filled immeidiately or cancelled. Filled until all improvement prices are filled.""" 
        order_id = next(self.order_id_counter)
        fok_order = Order(order_id, side, price, quantity)
        matching_book = self.bids if side =='ask' else self.asks
        
        if not matching_book:
            raise ValueError("No order avaialable in market.")
        
        matching_prices, total_quantity = self.liquidity_check(matching_book, fok_order) #Check for available liquidity at or below price

        if not matching_prices:
            return print(f"No orders available at or below price {price}. Order {order_id} cancelled.")
        
        if total_quantity < quantity:
            return print(f"Not enough liquidity available at or below price {price}. Order {order_id} cancelled.")
        
        #If enough liquidity is present, fill the order at the best prices available
        for price in matching_prices:
            orders = matching_book[price]
            fok_order.quantity = self.order_fill_logic(side, orders, fok_order.quantity)

            if fok_order.quantity == 0:  # Order fully filled
                print(f"Order {order_id} fully filled at price {price}.")
                return fok_order
            
            if not orders:
                del matching_book[price]

        return fok_order

    def immediate_or_cancel_order(self, side, price, quantity):
        """"Fill as much as possible at the best price, cancel the rest."""
        order_id = next(self.order_id_counter)
        ioc_order = Order(order_id, side, price, quantity)
        matching_book = self.bids if side == 'ask' else self.asks

        if not matching_book:
            return print(f"No orders available in market. Order {order_id} cancelled.")
        
        matching_prices, total_quantity = self.liquidity_check(matching_book, ioc_order)
        
        if not matching_prices:
            return print(f"No orders available at or below price {price}. Order {order_id} cancelled.")
        
        for match_price in matching_prices:
            orders = matching_book[match_price]
            ioc_order.quantity = self.order_fill_logic(side, orders, ioc_order.quantity)
            
            if not orders:
                del matching_book[match_price]
        
        if quantity > 0:
            filled_quantity = quantity - ioc_order.quantity
            print(f"Order {order_id} partially filled. Filled quantity: {filled_quantity}. Remaining quantity: {ioc_order.quantity}. Remaining Order cancelled.")
            return ioc_order
        else:
            print(f"Order {order_id} fully filled at price {match_price}.")
            return ioc_order

    def stop_order(self, side, stop_price, quantity):
        """Triggers market order once stop price is reached."""
        stop_order_id = next(self.order_id_counter)
        stop_order = StopOrder(stop_order_id, side, stop_price, quantity)
        book = self.bids if side == 'ask' else self.asks
        best_price = -book.peekitem(0)[0] if side == 'bid' else book.peekitem(0)[0]
        stop_market_orders = self.stop_market_orders_bid if side == 'bid' else self.stop_market_orders_ask

        # Check if book is empty
        if not book:
            stop_market_orders[stop_price] = deque() #Intialize a new deque if no orders exist at this stop price
            stop_market_orders[stop_price].append(stop_order)
            print(f"Stop order {stop_order_id} added at stop price {stop_price}.")

        #Chcek if stop price is reached
        if (side == 'bid' and stop_price >= best_price) or (side == 'ask' and stop_price <= best_price):
            # If stop price is reached, trigger market order
            print(f"Stop price {stop_price} reached. Triggering market order.")
            market_order = self.market_order(side, quantity)
            return market_order
        # If stop price not reached, add to stop orders market
        else:
            if stop_price not in stop_market_orders.keys():
                stop_market_orders[stop_price] = deque()
                stop_market_orders[stop_price].append(stop_order)
            print(f"Stop order {stop_order_id} added at stop price {stop_price}. Waiting for trigger.")

            return stop_order

    def stop_limit_order(self, side, stop_price, limit_price, quantity):
        """Triggers a limit order once stop price is reached."""
        stop_order_id = next(self.order_id_counter)
        stop_order = StopOrder(stop_order_id, side, stop_price, quantity)
        book = self.bids if side == 'ask' else self.asks
        best_price = book.peekitem(0)[0] if side == 'bid' else book.peekitem(-1)[0]

         # Check if book is empty
        if not book:
            self.stop_orders_limit[stop_price] = deque() #Intialize a new deque if no orders exist at this stop price
            self.stop_orders_limit[stop_price].append(stop_order)
            print(f"Stop order {stop_order_id} added at stop price {stop_price}.")

        #Chcek if stop price is reached
        if (side == 'bid' and stop_price >= best_price) or (side == 'ask' and stop_price <= best_price):
            # If stop price is reached, trigger market order
            print(f"Stop price, {stop_price} reached. Triggering Limit order.")
            limit_order = self.limit_order(side, limit_price, quantity)
            return limit_order
        
        # If stop price not reached, add to stop orders market
        else:
            if stop_price not in self.stop_orders_limit.keys():
                self.stop_orders_limit[stop_price] = deque()
            self.stop_orders_limit[stop_price].append(stop_order)
            print(f"Stop order {stop_order_id} added at stop price {stop_price}. Waiting for trigger.")

            return stop_order

