import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


# -------------------------------
# 1. DATA PREPARATION
# -------------------------------

def load_and_prepare_data(file_path):
    """
    Load dataset and perform preprocessing.
    """
    df = pd.read_csv(file_path)

    # Convert Date column
    df['Date'] = pd.to_datetime(df['Date'])

    # Extract useful features
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['DayOfWeek'] = df['Date'].dt.day_name()

    print("\n--- DATA INFO ---")
    print(df.info())
    print("\n--- FIRST 5 ROWS ---")
    print(df.head())

    return df


# -------------------------------
# 2. BASIC EXPLORATION
# -------------------------------

def basic_exploration(df):
    print("\n--- BASIC EXPLORATION ---")

    print("Total Transactions:", len(df))
    print("Unique Customers:", df['Customer_Name'].nunique())

    # Top products (split list)
    products = df['Product'].str.split(',').explode()
    print("\nTop 5 Products:")
    print(products.value_counts().head(5))

    print("\nTop Cities:")
    print(df['City'].value_counts().head())


# -------------------------------
# 3. CUSTOMER BEHAVIOUR
# -------------------------------

def customer_behavior(df):
    print("\n--- CUSTOMER BEHAVIOUR ---")

    # Avg spend by category
    avg_spend = df.groupby('Customer_Category')['Total_Cost'].mean()
    print("\nAverage Spend by Category:")
    print(avg_spend)

    # Payment preference
    payment_pref = pd.crosstab(df['Customer_Category'], df['Payment_Method'])
    print("\nPayment Preference:")
    print(payment_pref)

    # Avg items per store type
    avg_items = df.groupby('Store_Type')['Total_Items'].mean()
    print("\nAvg Items per Store Type:")
    print(avg_items)


# -------------------------------
# 4. PROMOTION & DISCOUNT
# -------------------------------

def promotion_analysis(df):
    print("\n--- PROMOTION ANALYSIS ---")

    # Discount impact
    discount_avg = df.groupby('Discount_Applied')['Total_Cost'].mean()
    print("\nAvg Cost (Discount vs No Discount):")
    print(discount_avg)

    # Items per promotion
    promo_items = df.groupby('Promotion')['Total_Items'].mean()
    print("\nAvg Items per Promotion:")
    print(promo_items)

    # Revenue impact
    promo_revenue = df.groupby('Promotion')['Total_Cost'].mean()
    print("\nRevenue per Promotion:")
    print(promo_revenue)


# -------------------------------
# 5. SEASONAL TRENDS
# -------------------------------

def seasonal_analysis(df):
    print("\n--- SEASONAL ANALYSIS ---")

    # Revenue by season
    season_revenue = df.groupby('Season')['Total_Cost'].sum()
    print("\nTotal Revenue by Season:")
    print(season_revenue)

    # Store preference
    season_store = pd.crosstab(df['Season'], df['Store_Type'])
    print("\nSeason vs Store Type:")
    print(season_store)

    # Plot avg spending per season
    plt.figure()
    sns.barplot(x='Season', y='Total_Cost', data=df)
    plt.title("Average Spending per Season")
    plt.xlabel("Season")
    plt.ylabel("Avg Cost")
    plt.show()

    print("Observation: Identify which season has highest average spending.")


# -------------------------------
# 6. VISUALIZATIONS
# -------------------------------

def create_visualizations(df):
    print("\n--- VISUALIZATIONS ---")

    # Transactions per city
    plt.figure()
    df['City'].value_counts().plot(kind='bar')
    plt.title("Transactions by City")
    plt.xlabel("City")
    plt.ylabel("Count")
    plt.show()
    print("Observation: Top cities drive most transactions.")

    # Payment distribution
    plt.figure()
    df['Payment_Method'].value_counts().plot(kind='pie', autopct='%1.1f%%')
    plt.title("Payment Method Distribution")
    plt.ylabel("")
    plt.show()
    print("Observation: Dominant payment method visible.")

    # Monthly revenue trend
    monthly = df.groupby(['Year', 'Month'])['Total_Cost'].sum().reset_index()

    plt.figure()
    sns.lineplot(x='Month', y='Total_Cost', hue='Year', data=monthly)
    plt.title("Monthly Revenue Trend")
    plt.show()
    print("Observation: Look for seasonality or spikes.")

    # Heatmap
    pivot = df.pivot_table(
        values='Total_Cost',
        index='Season',
        columns='Customer_Category',
        aggfunc='sum'
    )

    plt.figure()
    sns.heatmap(pivot, annot=True, fmt=".0f")
    plt.title("Revenue by Season & Customer Category")
    plt.show()
    print("Observation: Identify strongest segments.")


# -------------------------------
# MAIN EXECUTION
# -------------------------------

if __name__ == "__main__":
    # Get current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct file path (same folder)
    file_path = os.path.join(current_dir, "Retail_Transactions_Dataset-1.csv")
    #file_path = "Retail_Transactions_Dataset-1.csv"

    df = load_and_prepare_data(file_path)
    basic_exploration(df)
    customer_behavior(df)
    promotion_analysis(df)
    seasonal_analysis(df)
    create_visualizations(df)
