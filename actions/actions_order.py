from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from supabase import create_client
import random
import datetime
from typing import List, Dict
import boto3
import json

supabase = create_client("your-supabase-url", "your-supabase-key")
AWS_IOT = boto3.client('iot-data', region_name='us-east-1')

class ActionOrderFood(Action):
    def name(self) -> str:
        return "action_order_food"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> List[Dict]:
        product_tier = tracker.get_slot("product_tier") or "brick_chat"
        restaurant_id = tracker.get_slot("restaurant_id") or "default"
        pos_device_id = tracker.get_slot("pos_device_id") or "vilapos_default"
        food_item = tracker.get_slot("food_item") or "taco"
        quantity = tracker.get_slot("quantity") or "1"
        customization = tracker.get_slot("customization") or "standard"
        user_id = tracker.sender_id
        order_id = f"ORD-{random.randint(10000, 99999)}"
        eta = random.randint(15, 45)

        order = {
            "item": food_item,
            "quantity": int(quantity),
            "customization": customization,
            "order_id": order_id,
            "status": "pending",
            "eta": eta,
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "pos_device_id": pos_device_id,
            "timestamp": "now()"
        }
        supabase.table("orders").insert(order).execute()

        if product_tier in ["brick_core", "vilapro"]:
            supabase.table("inventory").update({"stock": lambda x: x - int(quantity)}).eq("item", food_item).eq("restaurant_id", restaurant_id).execute()
            supabase.channel('restaurant-notifs').send({'event': 'new_order', 'payload': order})
            AWS_IOT.publish(topic=f'pos/{pos_device_id}/print', payload=json.dumps({"order_id": order_id, "item": food_item, "quantity": quantity}))

        dispatcher.utter_message(response="utter_confirm_order", eta=eta)
        return [SlotSet("ordered_items", tracker.get_slot("ordered_items", []) + [order]), SlotSet("order_id", order_id)]
