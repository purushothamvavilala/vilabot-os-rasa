from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from supabase import create_client
import random
import datetime
import requests
import boto3
import json
from typing import List, Dict

supabase = create_client("your-supabase-url", "your-supabase-key")
AWS_IOT = boto3.client('iot-data', region_name='us-east-1')

class ActionOverseeOperations(Action):
    def name(self) -> str:
        return "action_oversee_operations"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> List[Dict]:
        product_tier = tracker.get_slot("product_tier") or "brick_chat"
        restaurant_id = tracker.get_slot("restaurant_id") or "default"
        pos_device_id = tracker.get_slot("pos_device_id") or "vilapos_default"
        orders = supabase.table("orders").select("*").eq("restaurant_id", restaurant_id).gte("timestamp", datetime.datetime.now().strftime("%Y-%m-%d 00:00")).execute().data
        tasks = supabase.table("tasks").select("*").eq("restaurant_id", restaurant_id).execute().data if product_tier in ["brick_core", "vilapro"] else []

        if product_tier == "brick_chat":
            dispatcher.utter_message(text="Brick Chat: Handling queries—upgrade for ViLaPOS automation!")
            return []

        # Simplified ETA check
        for order in orders:
            if order["eta"] < 20:
                supabase.table("tasks").insert({"employee": "SpotBot", "task": f"Expedite {order['order_id']}", "status": "assigned", "priority": "high", "restaurant_id": restaurant_id, "timestamp": "now()"}).execute()
                AWS_IOT.publish(topic=f'kitchen/{restaurant_id}/priority', payload=json.dumps({"order_id": order["order_id"]}))

        # ViLaPOS Sync
        if product_tier in ["brick_core", "vilapro"]:
            AWS_IOT.publish(topic=f'pos/{pos_device_id}/status', payload=json.dumps({"orders": len(orders)}))

        dispatcher.utter_message(text=f"Brick Ultra ({product_tier}): Optimized {len(orders)} orders, ViLaPOS synced!")
        return [SlotSet("product_tier", product_tier), SlotSet("pos_device_id", pos_device_id)]
