from .db_category import CategoryModel, Categoryx
from .db_item import ItemModel, Itemx
from .db_payments import PaymentsModel, Paymentsx
from .db_position import PositionModel, Positionx
from .db_purchases import PurchaseModel, Purchasesx
from .db_refill import RefillModel, Refillx
from .db_settings import SettingsModel, Settingsx
from .db_users import UserModel, UsersRepository, Userx
from .entities import Category, Item, Payments, Position, Purchase, Refill, Settings, User

ModelCategory = Category
ModelItem = Item
ModelPayments = Payments
ModelPosition = Position
ModelPurchases = Purchase
ModelRefill = Refill
ModelSettings = Settings
ModelUser = User
ModelUsers = User
SettingsRepository = Settingsx
