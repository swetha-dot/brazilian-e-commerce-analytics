import pandas as pd

# Load all tables
orders = pd.read_csv(r'C:\Users\hp\Documents\GitHub\tableau\analysis\dataset\olist_orders_dataset.csv')
order_items = pd.read_csv(r'C:\Users\hp\Documents\GitHub\tableau\analysis\dataset\olist_order_items_dataset.csv')
products = pd.read_csv(r'C:\Users\hp\Documents\GitHub\tableau\analysis\dataset\olist_products_dataset.csv')
customers = pd.read_csv(r'C:\Users\hp\Documents\GitHub\tableau\analysis\dataset\olist_customers_dataset.csv')
reviews = pd.read_csv(r'C:\Users\hp\Documents\GitHub\tableau\analysis\dataset\olist_order_reviews_dataset.csv')
payments = pd.read_csv(r'C:\Users\hp\Documents\GitHub\tableau\analysis\dataset\olist_order_payments_dataset.csv')
category_translation = pd.read_csv(r'C:\Users\hp\Documents\GitHub\tableau\analysis\dataset\product_category_name_translation.csv')

# Parse dates
date_cols = ['order_purchase_timestamp', 'order_delivered_customer_date',
             'order_estimated_delivery_date']
for col in date_cols:
    orders[col] = pd.to_datetime(orders[col])

# Keep delivered orders only
orders = orders[orders['order_status'] == 'delivered'].copy()
orders.dropna(subset=['order_delivered_customer_date',
                       'order_purchase_timestamp'], inplace=True)

# Merge everything into one flat table
df = orders.merge(order_items, on='order_id', how='left')
df = df.merge(products, on='product_id', how='left')
df = df.merge(category_translation, on='product_category_name', how='left')
df = df.merge(customers, on='customer_id', how='left')
df = df.merge(
    payments.groupby('order_id')['payment_value'].sum().reset_index(),
    on='order_id', how='left')
df = df.merge(
    reviews[['order_id','review_score']].drop_duplicates('order_id'),
    on='order_id', how='left')

# Feature engineering
df['order_month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
df['order_year']  = df['order_purchase_timestamp'].dt.year.astype(str)
df['delivery_days'] = (
    df['order_delivered_customer_date'] -
    df['order_purchase_timestamp']).dt.days
df['is_late'] = (
    df['order_delivered_customer_date'] >
    df['order_estimated_delivery_date']).astype(int)
df['category_english'] = df['product_category_name_english'].fillna('Unknown')

# Remove outliers
q = df['payment_value'].quantile(0.99)
df  = df[df['payment_value'] <= q]

# Save — Tableau needs CSV or Excel
df.to_csv(r'C:\Users\hp\Documents\GitHub\tableau\analysis\dataset\olist_tableau_ready.csv', index=False)
print(f"Saved: {df.shape[0]:,} rows, {df.shape[1]} columns")