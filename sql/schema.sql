-- =====================================================================
-- ZOMATO BUSINESS INTELLIGENCE & DELIVERY TIME PREDICTION PLATFORM
-- Database Schema (DDL)
-- Target engine: PostgreSQL 14+  (MySQL 8+ notes given where syntax differs)
-- =====================================================================
-- Load order matters because of foreign keys:
--   cities -> customers, restaurants, delivery_partners
--   restaurants -> menu
--   customers, restaurants, delivery_partners, promotions -> orders
--   orders, menu -> order_items
--   orders -> payments
--   orders -> customer_feedback
--   cities -> weather, traffic
--
-- NOTE ON RAW VS CLEANED LOADS:
-- The raw CSVs intentionally contain data-quality issues (nulls, duplicates,
-- orphaned foreign keys, malformed values). Load raw files into a staging
-- schema WITHOUT constraints first, clean them in Python/SQL, then load the
-- cleaned output into the constrained tables below. Attempting to load the
-- raw files directly into these tables will correctly fail on some rows --
-- that is expected and is part of the cleaning exercise.
-- =====================================================================

DROP TABLE IF EXISTS customer_feedback CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS menu CASCADE;
DROP TABLE IF EXISTS promotions CASCADE;
DROP TABLE IF EXISTS delivery_partners CASCADE;
DROP TABLE IF EXISTS restaurants CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS traffic CASCADE;
DROP TABLE IF EXISTS weather CASCADE;
DROP TABLE IF EXISTS cities CASCADE;

-- =====================================================================
-- 1. CITIES
-- =====================================================================
CREATE TABLE cities (
    CityID          INTEGER PRIMARY KEY,
    City            VARCHAR(100) NOT NULL UNIQUE,
    Population      BIGINT CHECK (Population > 0),
    Region          VARCHAR(50),
    AverageIncome   NUMERIC(12,2)
);

-- =====================================================================
-- 2. CUSTOMERS
-- =====================================================================
CREATE TABLE customers (
    CustomerID          INTEGER PRIMARY KEY,
    Name                VARCHAR(150) NOT NULL,
    Age                 SMALLINT CHECK (Age BETWEEN 0 AND 100),
    Gender              VARCHAR(20),
    Phone               VARCHAR(15),
    Email               VARCHAR(150),
    City                VARCHAR(100) NOT NULL,
    State               VARCHAR(100),
    Pincode             VARCHAR(10),
    RegistrationDate    DATE NOT NULL,
    Membership          VARCHAR(30),
    TotalOrders         INTEGER DEFAULT 0 CHECK (TotalOrders >= 0),
    PreferredCuisine    VARCHAR(50),
    CONSTRAINT fk_customers_city FOREIGN KEY (City) REFERENCES cities(City)
);

-- =====================================================================
-- 3. RESTAURANTS
-- =====================================================================
CREATE TABLE restaurants (
    RestaurantID    INTEGER PRIMARY KEY,
    RestaurantName  VARCHAR(150) NOT NULL,
    Cuisine         VARCHAR(50),
    City            VARCHAR(100) NOT NULL,
    Area            VARCHAR(100),
    OpeningTime     TIME,
    ClosingTime     TIME,
    Rating          NUMERIC(2,1) CHECK (Rating BETWEEN 1.0 AND 5.0),
    AverageCost     NUMERIC(10,2) CHECK (AverageCost >= 0),
    OwnerName       VARCHAR(150),
    RestaurantType  VARCHAR(50),
    Latitude        NUMERIC(9,6),
    Longitude       NUMERIC(9,6),
    CONSTRAINT fk_restaurants_city FOREIGN KEY (City) REFERENCES cities(City)
);

-- =====================================================================
-- 4. MENU
-- =====================================================================
CREATE TABLE menu (
    FoodItemID      INTEGER PRIMARY KEY,
    RestaurantID    INTEGER NOT NULL,
    FoodName        VARCHAR(150) NOT NULL,
    Category        VARCHAR(50),
    Price           NUMERIC(10,2) CHECK (Price >= 0),
    PreparationTime SMALLINT CHECK (PreparationTime >= 0),
    Calories        SMALLINT,
    Availability    VARCHAR(5),
    CONSTRAINT fk_menu_restaurant FOREIGN KEY (RestaurantID) REFERENCES restaurants(RestaurantID)
);

-- =====================================================================
-- 5. DELIVERY_PARTNERS
-- =====================================================================
CREATE TABLE delivery_partners (
    DeliveryPartnerID   INTEGER PRIMARY KEY,
    Name                VARCHAR(150) NOT NULL,
    Age                 SMALLINT CHECK (Age BETWEEN 16 AND 70),
    Gender              VARCHAR(20),
    VehicleType         VARCHAR(30),
    JoiningDate         DATE,
    City                VARCHAR(100) NOT NULL,
    Rating              NUMERIC(2,1) CHECK (Rating BETWEEN 1.0 AND 5.0),
    CompletedDeliveries INTEGER DEFAULT 0 CHECK (CompletedDeliveries >= 0),
    AverageDeliveryTime NUMERIC(6,2) CHECK (AverageDeliveryTime >= 0),
    CONSTRAINT fk_dp_city FOREIGN KEY (City) REFERENCES cities(City)
);

-- =====================================================================
-- 6. PROMOTIONS
-- =====================================================================
CREATE TABLE promotions (
    PromotionID         INTEGER PRIMARY KEY,
    CouponCode          VARCHAR(20) NOT NULL UNIQUE,
    DiscountPercentage  SMALLINT CHECK (DiscountPercentage BETWEEN 0 AND 100),
    CampaignName        VARCHAR(150),
    StartDate           DATE NOT NULL,
    EndDate             DATE NOT NULL,
    CONSTRAINT chk_promo_dates CHECK (EndDate >= StartDate)
);

-- =====================================================================
-- 7. ORDERS
-- =====================================================================
CREATE TABLE orders (
    OrderID             INTEGER PRIMARY KEY,
    CustomerID          INTEGER NOT NULL,
    RestaurantID        INTEGER NOT NULL,
    DeliveryPartnerID   INTEGER NOT NULL,
    OrderDate           DATE NOT NULL,
    OrderTime           TIME NOT NULL,
    DeliveryTimeMinutes SMALLINT CHECK (DeliveryTimeMinutes >= 0),
    FoodCost            NUMERIC(10,2) CHECK (FoodCost >= 0),
    DeliveryFee         NUMERIC(8,2)  CHECK (DeliveryFee >= 0),
    Discount            NUMERIC(8,2)  DEFAULT 0 CHECK (Discount >= 0),
    CouponCode          VARCHAR(20),
    GST                 NUMERIC(8,2)  DEFAULT 0 CHECK (GST >= 0),
    FinalAmount         NUMERIC(10,2) CHECK (FinalAmount >= 0),
    OrderStatus         VARCHAR(30) NOT NULL,
    PaymentMethod       VARCHAR(30),
    CONSTRAINT fk_orders_customer   FOREIGN KEY (CustomerID)        REFERENCES customers(CustomerID),
    CONSTRAINT fk_orders_restaurant FOREIGN KEY (RestaurantID)      REFERENCES restaurants(RestaurantID),
    CONSTRAINT fk_orders_dp         FOREIGN KEY (DeliveryPartnerID) REFERENCES delivery_partners(DeliveryPartnerID),
    CONSTRAINT fk_orders_coupon     FOREIGN KEY (CouponCode)        REFERENCES promotions(CouponCode)
);

-- =====================================================================
-- 8. ORDER_ITEMS
-- =====================================================================
CREATE TABLE order_items (
    OrderItemID     INTEGER PRIMARY KEY,
    OrderID         INTEGER NOT NULL,
    FoodItemID      INTEGER NOT NULL,
    Quantity        SMALLINT CHECK (Quantity > 0),
    UnitPrice       NUMERIC(10,2) CHECK (UnitPrice >= 0),
    TotalPrice      NUMERIC(10,2) CHECK (TotalPrice >= 0),
    CONSTRAINT fk_oi_order FOREIGN KEY (OrderID)    REFERENCES orders(OrderID),
    CONSTRAINT fk_oi_food  FOREIGN KEY (FoodItemID) REFERENCES menu(FoodItemID)
);

-- =====================================================================
-- 9. PAYMENTS
-- =====================================================================
CREATE TABLE payments (
    PaymentID       INTEGER PRIMARY KEY,
    OrderID         INTEGER NOT NULL,
    PaymentMethod   VARCHAR(30),
    PaymentStatus   VARCHAR(20),
    TransactionID   VARCHAR(30),
    PaymentDate     DATE,
    CONSTRAINT fk_payments_order FOREIGN KEY (OrderID) REFERENCES orders(OrderID)
);

-- =====================================================================
-- 10. CUSTOMER_FEEDBACK
-- =====================================================================
CREATE TABLE customer_feedback (
    FeedbackID      INTEGER PRIMARY KEY,
    OrderID         INTEGER NOT NULL,
    CustomerRating  SMALLINT CHECK (CustomerRating BETWEEN 1 AND 5),
    DeliveryRating  SMALLINT CHECK (DeliveryRating BETWEEN 1 AND 5),
    FoodRating      SMALLINT CHECK (FoodRating BETWEEN 1 AND 5),
    Review          TEXT,
    Sentiment       VARCHAR(20),
    CONSTRAINT fk_feedback_order FOREIGN KEY (OrderID) REFERENCES orders(OrderID)
);

-- =====================================================================
-- 11. WEATHER
-- =====================================================================
CREATE TABLE weather (
    WeatherID           INTEGER PRIMARY KEY,
    City                VARCHAR(100) NOT NULL,
    Date                DATE NOT NULL,
    Temperature         NUMERIC(5,2),
    Rainfall            NUMERIC(6,2),
    Humidity            SMALLINT,
    WeatherCondition    VARCHAR(30),
    CONSTRAINT fk_weather_city FOREIGN KEY (City) REFERENCES cities(City)
);

-- =====================================================================
-- 12. TRAFFIC
-- =====================================================================
CREATE TABLE traffic (
    TrafficID       INTEGER PRIMARY KEY,
    City            VARCHAR(100) NOT NULL,
    Date            DATE NOT NULL,
    Time            TIME NOT NULL,
    TrafficLevel    VARCHAR(20),
    AverageSpeed    NUMERIC(5,2),
    CONSTRAINT fk_traffic_city FOREIGN KEY (City) REFERENCES cities(City)
);

-- =====================================================================
-- INDEXES
-- (beyond the automatic indexes Postgres creates for PK/UNIQUE constraints)
-- =====================================================================

-- Speeds up the very common "orders by customer" and "orders by date range" filters
CREATE INDEX idx_orders_customer_date ON orders(CustomerID, OrderDate);

-- Speeds up restaurant-level revenue/rating rollups
CREATE INDEX idx_orders_restaurant ON orders(RestaurantID);

-- Speeds up delivery-partner performance rollups
CREATE INDEX idx_orders_deliverypartner ON orders(DeliveryPartnerID);

-- Speeds up joining weather/traffic to orders by city + date
CREATE INDEX idx_weather_city_date ON weather(City, Date);
CREATE INDEX idx_traffic_city_date ON traffic(City, Date);

-- =====================================================================
-- SAMPLE DATA (illustrative rows only -- bulk load happens from the
-- cleaned CSVs via COPY / LOAD DATA, not from these INSERTs)
-- =====================================================================

-- =====================================================================
-- COPY EXAMPLES (PostgreSQL) -- run these after creating the tables to
-- load the CLEANED CSVs produced in the Python stage.
-- =====================================================================

-- Run all your COPY statements in order
COPY cities FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/cities_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY customers FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/customers_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY restaurants FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/restaurants_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY delivery_partners FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/delivery_partners_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY promotions FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/promotions_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY menu FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/menu_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY orders FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/orders_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY order_items FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/order_items_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY payments FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/payments_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY customer_feedback FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/customer_feedback_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY weather FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/weather_cleaned.csv' WITH (FORMAT csv, HEADER true);
COPY traffic FROM '/Users/Priyanka/Documents/Internship-Internmo/Zomato_BI_Project/data/cleaned/traffic_cleaned.csv' WITH (FORMAT csv, HEADER true);



-- MySQL 8+ equivalent notes:
--   * Replace SERIAL-style expectations with INT AUTO_INCREMENT if you want
--     auto-generated keys instead of loading explicit IDs.
--   * Replace \copy with: LOAD DATA LOCAL INFILE 'path/file.csv'
--       INTO TABLE table_name
--       FIELDS TERMINATED BY ',' ENCLOSED BY '"'
--       LINES TERMINATED BY '\n'
--       IGNORE 1 ROWS;
--   * CHECK constraints are enforced in MySQL 8.0.16+; on older versions
--     they are parsed but not enforced -- validate in Python instead.
SELECT 'Schema created and cleaned data loaded successfully.' AS status;

SELECT * FROM cities LIMIT 5;
SELECT * FROM customers LIMIT 5;
SELECT * FROM restaurants LIMIT 5;
SELECT * FROM delivery_partners LIMIT 5;
SELECT * FROM promotions LIMIT 5;
SELECT * FROM menu LIMIT 5;
SELECT * FROM orders LIMIT 5;
SELECT * FROM order_items LIMIT 5;
SELECT * FROM payments LIMIT 5;
SELECT * FROM customer_feedback LIMIT 5;
SELECT * FROM weather LIMIT 5;
SELECT * FROM traffic LIMIT 5;