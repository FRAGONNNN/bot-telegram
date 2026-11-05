# - *- coding: utf- 8 - *-
from dataclasses import dataclass


@dataclass
class Category:
    increment: int
    category_id: int
    category_name: str
    category_unix: int


@dataclass
class Position:
    increment: int
    category_id: int
    position_id: int
    position_name: str
    position_price: float
    position_desc: str
    position_photo: str
    position_unix: int


@dataclass
class Item:
    increment: int
    user_id: int
    category_id: int
    position_id: int
    item_id: int
    item_unix: int
    item_data: str


@dataclass
class Payments:
    id: int
    cryptobot_token: str
    yoomoney_token: str
    stars_course: float
    status_cryptobot: str
    status_yoomoney: str
    status_stars: str


@dataclass
class Purchase:
    increment: int
    user_id: int
    user_balance_before: float
    user_balance_after: float
    purchase_receipt: int
    purchase_data: str
    purchase_count: int
    purchase_price: float
    purchase_price_one: float
    purchase_position_id: int
    purchase_position_name: str
    purchase_category_id: int
    purchase_category_name: str
    purchase_unix: int


@dataclass
class Refill:
    increment: int
    user_id: int
    refill_receipt: int
    refill_comment: str
    refill_amount: float
    refill_method: str
    refill_unix: int


@dataclass
class Settings:
    id: int
    status_work: str
    status_refill: str
    status_buy: str
    notification_refill: str
    notification_buy: str
    misc_faq: str
    misc_support: str
    misc_bot: str
    misc_hosting_text: str
    misc_token_telegraph: str
    misc_discord_webhook_url: str
    misc_discord_webhook_name: str
    misc_hide_category: str
    misc_hide_position: str
    misc_method_prod: str
    misc_profit_day: int
    misc_profit_week: int
    misc_profit_month: int


@dataclass
class User:
    increment: int
    user_id: int
    user_login: str
    user_name: str
    user_surname: str
    user_fullname: str
    user_balance: float
    user_refill: float
    user_give: float
    user_unix: int
