# Data Quality Audit Log
## Over-all raw inpection on csv files
```
File: customers.csv
    - Shape: (12180, 13)
    - Columns: ['CustomerID', 'Name', 'Age', 'Gender', 'Phone', 'Email', 'City', 'State', 'Pincode', 'RegistrationDate', 'Membership', 'TotalOrders', 'PreferredCuisine']
    - Duplicates: 180
----------------------------------------
    - Missing Values:
      - Age: 170 (1.4%)
      - Gender: 122 (1.0%)
      - Phone: 144 (1.2%)
      - Email: 332 (2.7%)
      - State: 186 (1.5%)
      - Membership: 120 (1.0%)
      - PreferredCuisine: 245 (2.0%)

File: delivery_partners.csv
    - Shape: (2000, 10)
    - Columns: ['DeliveryPartnerID', 'Name', 'Age', 'Gender', 'VehicleType', 'JoiningDate', 'City', 'Rating', 'CompletedDeliveries', 'AverageDeliveryTime']
    - Duplicates: 0
----------------------------------------
    - Missing Values:
      - Rating: 34 (1.7%)

File: orders.csv
    - Shape: (20705, 15)
    - Columns: ['OrderID', 'CustomerID', 'RestaurantID', 'DeliveryPartnerID', 'OrderDate', 'OrderTime', 'DeliveryTimeMinutes', 'FoodCost', 'DeliveryFee', 'Discount', 'CouponCode', 'GST', 'FinalAmount', 'OrderStatus', 'PaymentMethod']
    - Duplicates: 205
----------------------------------------
    - Missing Values:
      - CouponCode: 13421 (64.8%)
      - FinalAmount: 327 (1.6%)

File: menu.csv
    - Shape: (8997, 8)
    - Columns: ['FoodItemID', 'RestaurantID', 'FoodName', 'Category', 'Price', 'PreparationTime', 'Calories', 'Availability']
    - Duplicates: 0
----------------------------------------
    - Missing Values:
      - Calories: 132 (1.5%)

File: traffic.csv
    - Shape: (18335, 6)
    - Columns: ['TrafficID', 'City', 'Date', 'Time', 'TrafficLevel', 'AverageSpeed']
    - Duplicates: 0
----------------------------------------
    - Missing Values:
      - TrafficLevel: 147 (0.8%)

File: promotions.csv
    - Shape: (300, 6)
    - Columns: ['PromotionID', 'CouponCode', 'DiscountPercentage', 'CampaignName', 'StartDate', 'EndDate']
    - Duplicates: 0
----------------------------------------
    - No missing values found.

File: payments.csv
    - Shape: (20493, 6)
    - Columns: ['PaymentID', 'OrderID', 'PaymentMethod', 'PaymentStatus', 'TransactionID', 'PaymentDate']
    - Duplicates: 0
----------------------------------------
    - Missing Values:
      - TransactionID: 183 (0.9%)

File: cities.csv
    - Shape: (25, 5)
    - Columns: ['CityID', 'City', 'Population', 'Region', 'AverageIncome']
    - Duplicates: 0
----------------------------------------
    - Missing Values:
      - AverageIncome: 2 (8.0%)

File: weather.csv
    - Shape: (18264, 7)
    - Columns: ['WeatherID', 'City', 'Date', 'Temperature', 'Rainfall', 'Humidity', 'WeatherCondition']
    - Duplicates: 0
----------------------------------------
    - Missing Values:
      - City: 91 (0.5%)
      - Rainfall: 269 (1.5%)

File: customer_feedback.csv
    - Shape: (14200, 7)
    - Columns: ['FeedbackID', 'OrderID', 'CustomerRating', 'DeliveryRating', 'FoodRating', 'Review', 'Sentiment']
    - Duplicates: 0
----------------------------------------
    - Missing Values:
      - CustomerRating: 294 (2.1%)
      - Review: 1058 (7.5%)

File: order_items.csv
    - Shape: (42378, 6)
    - Columns: ['OrderItemID', 'OrderID', 'FoodItemID', 'Quantity', 'UnitPrice', 'TotalPrice']
    - Duplicates: 0
----------------------------------------
    - Missing Values:
      - TotalPrice: 435 (1.0%)

File: restaurants.csv
    - Shape: (1200, 13)
    - Columns: ['RestaurantID', 'RestaurantName', 'Cuisine', 'City', 'Area', 'OpeningTime', 'ClosingTime', 'Rating', 'AverageCost', 'OwnerName', 'RestaurantType', 'Latitude', 'Longitude']
    - Duplicates: 0
----------------------------------------
    - Missing Values:
      - Cuisine: 12 (1.0%)
      - Rating: 22 (1.8%)
```
## 1. Orders dataset (orders.csv)
### Summary of findings
- **Missing Values:** `CouponCode` (13421 rows), `FinalAmount`(327 rows)
- **Duplicates:** 205
- **Formatting Issues:** None
- **Invalid Values:** `DeliveryTimeMinutes`(min: -91) and `FoodCost`(min: -811) have -ve values
- **Datatype Mismatch:** 
    - `OrderDate` str to datetime and `OrderTime` str to time format
    - `CustomerID`, `OrderID`, `RestaurantID` convert int64 to str to prevent numerical operations
    - `FoodCost` & `DeliveryFee` convert from int64 to float64
- **Extreme Outliers:** 
    - `DeliveryTimeMinutes` (max: 399) with 1219 outliers above IQR
    - `Discount` (max: 416.5) wtih 1768 outliers 
    - `FoodCost` (max: 968) with 250 outliers
    - `GST` & `FinalAmount` with 69 and 78 outliers respectively
### Raw Profiling Output
```
==================================================
DETAILED PROFILE OF ORDERS:
==================================================

---Data Types and Data Completeness---
                    DataType  Non-Null Count  Missing Count  \
OrderID                int64           20705              0   
CustomerID             int64           20705              0   
RestaurantID           int64           20705              0   
DeliveryPartnerID      int64           20705              0   
OrderDate                str           20705              0   
OrderTime                str           20705              0   
DeliveryTimeMinutes    int64           20705              0   
FoodCost               int64           20705              0   
DeliveryFee            int64           20705              0   
Discount             float64           20705              0   
CouponCode               str            7284          13421   
GST                  float64           20705              0   
FinalAmount          float64           20378            327   
OrderStatus              str           20705              0   
PaymentMethod            str           20705              0   

                     Missing Percentage  
OrderID                            0.00  
CustomerID                         0.00  
RestaurantID                       0.00  
DeliveryPartnerID                  0.00  
OrderDate                          0.00  
OrderTime                          0.00  
DeliveryTimeMinutes                0.00  
FoodCost                           0.00  
DeliveryFee                        0.00  
Discount                           0.00  
CouponCode                        64.82  
GST                                0.00  
FinalAmount                        1.58  
OrderStatus                        0.00  
PaymentMethod                      0.00  

---Numeric Summary Statistics---
                       count       mean      std       min       25%  \
OrderID              20705.0  110252.61  5919.75  100001.0  105122.0   
CustomerID           20705.0    5966.38  3486.12       1.0    2911.0   
RestaurantID         20705.0     602.77   348.33       1.0     303.0   
DeliveryPartnerID    20705.0    1003.81   577.58       1.0     501.0   
DeliveryTimeMinutes  20705.0      37.87    27.45     -93.0      27.0   
FoodCost             20705.0     375.68   172.62    -811.0     269.0   
DeliveryFee          20705.0      27.43    15.52       0.0      20.0   
Discount             20705.0      37.13    64.52       0.0       0.0   
GST                  20705.0      19.12     7.85       3.0      13.6   
FinalAmount          20378.0     392.14   163.41      33.0     273.1   

                           50%        75%       max       IQR  Outliers  
OrderID              110255.00  115385.00  120500.0  10263.00         0  
CustomerID             5908.00    9023.00   12470.0   6112.00         0  
RestaurantID            600.00     904.00    1391.0    601.00         0  
DeliveryPartnerID      1008.00    1504.00    2000.0   1003.00         0  
DeliveryTimeMinutes      35.00      43.00     399.0     16.00      1219  
FoodCost                378.00     488.00     968.0    219.00       250  
DeliveryFee              30.00      40.00      49.0     20.00         0  
Discount                  0.00      58.80     416.5     58.80      1768  
GST                      19.05      24.45      48.4     10.85        69  
FinalAmount             383.30     502.95    1011.2    229.85        78  

---Categorical Summary Statistics---

Value Counts for 'OrderStatus':
OrderStatus
Delivered             11517
Cancelled              4625
Food Not Delivered     2386
Delivered Late         2177
Name: count, dtype: int64

Value Counts for 'PaymentMethod':
PaymentMethod
Debit Card          3565
Net Banking         3494
Cash on Delivery    3487
UPI                 3392
Credit Card         3388
Wallet              3379
Name: count, dtype: int64

Value Counts for 'CouponCode':
CouponCode
NaN         13421
ZOMXA87K       39
ZOMGN2K6       39
ZOMBQZT6       38
ZOM6B4AP       36
            ...  
ZOMDLTN4       16
ZOM5KTJY       16
ZOM9LF9G       15
ZOMNZ79M       14
ZOM4CA2P       13
Name: count, Length: 301, dtype: int64

================================================== 
```
## 2. Restaurants dataset (restaurants.csv)
### Summary of findings
- **Missing Values:** `Cuisine`(12 rows) & `Rating`(22 rows)
- **Duplicates:** None
- **Formatting Issues:** 
    -`City` contains inconsistent uppercase strings and trailing whitespaces
    -`RestaurantName` with trailing whitespaces
- **Invalid Values:** 
    - `AverageCost`(min: -894) has -ve values
    - `Rating`(max: 9.8) impossible since scale is 1.0-5.0
- **Datatype Mismatch:** 
    - `OpeningTime` and `ClosingTime` str to time format
    - `AverageCost` from int64 to float64
    - `RestaurantID` convert int64 to str to prevent numerical operations
- **Extreme Outliers:** 
    - `Rating` with 26 can be rescaled or NaN.
    -`AverageCost` with 18 outliers (max: 1065)

### Raw Profiling Output
```text
==================================================
DETAILED PROFILE OF RESTAURANTS:
==================================================

---Data Types and Data Completeness---
               DataType  Non-Null Count  Missing Count  Missing Percentage
RestaurantID      int64            1200              0                0.00
RestaurantName      str            1200              0                0.00
Cuisine             str            1188             12                1.00
City                str            1200              0                0.00
Area                str            1200              0                0.00
OpeningTime         str            1200              0                0.00
ClosingTime         str            1200              0                0.00
Rating          float64            1178             22                1.83
AverageCost       int64            1200              0                0.00
OwnerName           str            1200              0                0.00
RestaurantType      str            1200              0                0.00
Latitude        float64            1200              0                0.00
Longitude       float64            1200              0                0.00

---Numeric Summary Statistics---
               count    mean     std     min     25%     50%     75%      max  \
RestaurantID  1200.0  600.50  346.55    1.00  300.75  600.50  900.25  1200.00   
Rating        1178.0    3.94    0.72    2.30    3.60    3.90    4.20     9.80   
AverageCost   1200.0  446.86  220.80 -894.00  316.00  456.50  592.00  1065.00   
Latitude      1200.0   21.23    7.56    8.04   14.69   21.27   27.99    33.92   
Longitude     1200.0   79.79    5.62   70.01   74.81   80.12   84.93    88.97   

                 IQR  Outliers  
RestaurantID  599.50         0  
Rating          0.60        26  
AverageCost   276.00        18  
Latitude       13.30         0  
Longitude      10.12         0  

---Categorical Summary Statistics---

Value Counts for 'RestaurantName':
RestaurantName
The House           22
Green Corner        19
Urban House         18
Grand Kitchen       18
Curry Cafe          17
                    ..
urban treats         1
spicy point          1
 Golden Treats       1
GOLDEN CORNER        1
CURRY KITCHEN        1
Name: count, Length: 154, dtype: int64

Value Counts for 'Cuisine':
Cuisine
South Indian    81
Fast Food       76
Healthy Food    75
Street Food     70
Desserts        66
Continental     66
Seafood         65
Sushi           64
Pizza           61
Mughlai         59
Italian         59
BBQ             59
Burgers         58
Biryani         58
Mexican         58
North Indian    58
Chinese         55
Bakery          50
Thai            50
NaN             12
Name: count, dtype: int64

Value Counts for 'City':
City
Pune             53
Delhi            51
Ahmedabad        51
Surat            50
Bhopal           49
                 ..
NASHIK            1
KOCHI             1
VISAKHAPATNAM     1
 Hyderabad        1
 Mumbai           1
Name: count, Length: 91, dtype: int64

Value Counts for 'Area':
Area
Civil Lines     114
Lake View       108
Station Road    107
Park Street     105
Central         104
Market Area     102
Ring Road       102
Old Town        102
MG Road          94
New Town         91
Hill Road        90
Sector 12        81
Name: count, dtype: int64

Value Counts for 'OwnerName':
OwnerName
Qarin Ray            1
Manan Bala           1
Nicholas Manne       1
Harsh Bhargava       1
Daksha Narayanan     1
                    ..
Yashoda Rastogi      1
Azaan Bhagat         1
Jackson Chaudhary    1
Pahal Bose           1
Harshil Menon        1
Name: count, Length: 1200, dtype: int64

Value Counts for 'RestaurantType':
RestaurantType
Cloud Kitchen         251
Dine-in               246
Delivery Only         244
QSR                   237
Dine-in & Delivery    222
Name: count, dtype: int64

==================================================

```
## 3. Customers dataset (customers.csv)
### Summary of findings
- **Missing Values:** 
    -`Age`(170 rows),`Gender`(122 rows),`Phone`(144 rows),`Email`(332 rows), 
    -`State`(186 rows),`Membership`(120 rows),`PreferredCuisine`(245 rows)
- **Duplicates:** 180
- **Formatting Issues:** 
    -`City` contains inconsistent uppercase strings and trailing whitespaces
    -`Area` contains trailing whitespaces
    -`Pincode` needs to be valid and remove invalid ones like -ve ones
    -`Name` contains trailing whitespaces
    -`Phone` needs to be standardized, some contain malformed data
- **Invalid Values:** `Age`(min: -54) which is impossible, `Phone` needs to be standardized
- **Datatype Mismatch:** 
    -`Age` to be converted from float64 to int64 after handling missing values
    -`RegistrationDate` to be converted from str to datetime format
    -`CustomerID` convert int64 to str to prevent numerical operations

- **Extreme Outliers:** 
    - `Age` with 299 outliers
    - `TotalOrders` with 252 outliers
### Raw Profiling Output
```text
==================================================
DETAILED PROFILE OF CUSTOMERS:
==================================================

---Data Types and Data Completeness---
                 DataType  Non-Null Count  Missing Count  Missing Percentage
CustomerID          int64           12180              0                0.00
Name                  str           12180              0                0.00
Age               float64           12010            170                1.40
Gender                str           12058            122                1.00
Phone                 str           12036            144                1.18
Email                 str           11848            332                2.73
City                  str           12180              0                0.00
State                 str           11994            186                1.53
Pincode               str           12180              0                0.00
RegistrationDate      str           12180              0                0.00
Membership            str           12060            120                0.99
TotalOrders         int64           12180              0                0.00
PreferredCuisine      str           11935            245                2.01

---Numeric Summary Statistics---
               count     mean      std   min      25%     50%      75%  \
CustomerID   12180.0  5999.63  3464.51   1.0  3002.75  5996.5  9003.25   
Age          12010.0    29.44    12.34 -54.0    24.00    30.0    36.00   
TotalOrders  12180.0     5.99     2.45   0.0     4.00     6.0     7.00   

                 max     IQR  Outliers  
CustomerID   12000.0  6000.5         0  
Age             66.0    12.0       299  
TotalOrders     19.0     3.0       252  

---Categorical Summary Statistics---

Value Counts for 'Name':
Name
Janani Mani             3
Varenya Joshi           3
Rohan Buch              3
Charan Mukhopadhyay     3
Janaki Sood             3
                       ..
Isaiah Kapur            1
Anjali Bhattacharyya    1
Odika Saraf             1
Harshil Nori            1
Chakradev Sandal        1
Name: count, Length: 11760, dtype: int64

Value Counts for 'Gender':
Gender
Female    4054
Other     4003
Male      4001
NaN        122
Name: count, dtype: int64

Value Counts for 'City':
City
Bhubaneswar      486
Chandigarh       483
Hyderabad        480
Raipur           475
Coimbatore       474
                ... 
 Chandigarh        8
JAIPUR             7
HYDERABAD          6
 Vadodara          5
GUWAHATI           3
Name: count, Length: 109, dtype: int64

Value Counts for 'Membership':
Membership
Basic         7174
Zomato Pro    2490
Gold          2396
NaN            120
Name: count, dtype: int64

Value Counts for 'PreferredCuisine':
PreferredCuisine
North Indian    900
Desserts        892
Mughlai         885
Mexican         868
Thai            858
Bakery          855
South Indian    850
Street Food     847
Italian         846
Fast Food       842
Healthy Food    842
Chinese         822
Biryani         818
Continental     810
NaN             245
Name: count, dtype: int64

Value Counts for 'State':
State
Arunachal Pradesh    470
Punjab               460
Himachal Pradesh     457
Tripura              456
Maharashtra          451
Gujarat              448
West Bengal          442
Uttar Pradesh        441
Tamil Nadu           441
Chhattisgarh         440
Sikkim               436
Goa                  435
Andhra Pradesh       434
Bihar                434
Kerala               434
Madhya Pradesh       433
Rajasthan            431
Manipur              419
Nagaland             416
Mizoram              412
Haryana              411
Telangana            407
Karnataka            402
Odisha               402
Assam                399
Uttarakhand          396
Jharkhand            396
Meghalaya            391
NaN                  186
Name: count, dtype: int64

Value Counts for 'Pincode':
Pincode
000000     126
-110001    120
276847       3
432835       3
153861       2
          ... 
232354       1
828775       1
853369       1
521915       1
229577       1
Name: count, Length: 11667, dtype: int64

==================================================
```
## 4. Delivery Partners dataset (delivery_partners.csv)
### Summary of findings
- **Missing Values:** `Rating`(34 rows)
- **Duplicates:** None
- **Formatting Issues:** 
    -`City` contains inconsistent uppercase strings and trailing whitespaces
    -`Name` contains trailing whitespaces
- **Invalid Values:** `AverageDeliveryTime` has -ve impossible values like (min: -52.7)
- **Datatype Mismatch:** 
    -`JoiningDate` need to parse it to datetime from str
    -`DeliveryPartnerID` convert int64 to str to prevent numerical operations

**Extreme Outliers:** 
    - `Age` with 17 outliers
    - `Rating` with 3 outliers
    - `CompletedDeliveries` with 39 outliers
    - `AverageDeliveryTime` with 32 outliers
### Raw Profiling Output
```text
==================================================
DETAILED PROFILE OF DELIVERY PARTNERS:
==================================================

---Data Types and Data Completeness---
                    DataType  Non-Null Count  Missing Count  \
DeliveryPartnerID      int64            2000              0   
Name                     str            2000              0   
Age                    int64            2000              0   
Gender                   str            2000              0   
VehicleType              str            2000              0   
JoiningDate              str            2000              0   
City                     str            2000              0   
Rating               float64            1966             34   
CompletedDeliveries    int64            2000              0   
AverageDeliveryTime  float64            2000              0   

                     Missing Percentage  
DeliveryPartnerID                   0.0  
Name                                0.0  
Age                                 0.0  
Gender                              0.0  
VehicleType                         0.0  
JoiningDate                         0.0  
City                                0.0  
Rating                              1.7  
CompletedDeliveries                 0.0  
AverageDeliveryTime                 0.0  

---Numeric Summary Statistics---
                      count     mean     std   min     25%     50%      75%  \
DeliveryPartnerID    2000.0  1000.50  577.49   1.0  500.75  1000.5  1500.25   
Age                  2000.0    27.64    5.60  18.0   24.00    28.0    31.00   
Rating               1966.0     4.19    0.39   2.8    3.90     4.2     4.50   
CompletedDeliveries  2000.0   609.45  303.90  43.0  385.00   559.0   775.00   
AverageDeliveryTime  2000.0    31.50   11.70 -52.7   25.80    32.3    38.42   

                        max     IQR  Outliers  
DeliveryPartnerID    2000.0  999.50         0  
Age                    47.0    7.00        17  
Rating                  5.0    0.60         3  
CompletedDeliveries  2136.0  390.00        39  
AverageDeliveryTime    64.2   12.62        32  

---Categorical Summary Statistics---

Value Counts for 'Name':
Name
Tanmayi Baral       2
Nitesh Devi         2
Vasatika Goda       2
Fariq Chanda        2
Yashvi Venkatesh    2
                   ..
Chaaya Narang       1
Faqid Mannan        1
Krisha Ghose        1
Ishani Shetty       1
Max Kapur           1
Name: count, Length: 1993, dtype: int64

Value Counts for 'VehicleType':
VehicleType
Bike       1126
Scooter     491
Bicycle     192
Car         191
Name: count, dtype: int64

Value Counts for 'City':
City
Kochi            97
Pune             94
Patna            89
Visakhapatnam    84
Ludhiana         83
                 ..
visakhapatnam     1
patna             1
nashik            1
 Mumbai           1
 Chennai          1
Name: count, Length: 100, dtype: int64

Value Counts for 'Gender':
Gender
Male      1003
Female     997
Name: count, dtype: int64

==================================================

```
## 5. Menu dataset (menu.csv)
### Summary of findings
- **Missing Values:** `Calories` (132 rows)
- **Duplicates:** None
- **Formatting Issues:** `FoodName` has trailing whitespaces and inconsistent upper case strings
- **Invalid Values:** `Price` has -ve values (min: -358.0)
- **Datatype Mismatch:** 
    -`Price` convert from int64 to float64
    -`FoodItemID` & `RestaurantID` convert int64 to str to prevent numerical operations
- **Extreme Outliers:** 
    - `Price` with 107 outliers
    - `PreparationTime` with 23 outliers
    - `Calories` with 38 outliers
### Raw Profiling Output
```text
==================================================
DETAILED PROFILE OF MENU:
==================================================

---Data Types and Data Completeness---
                DataType  Non-Null Count  Missing Count  Missing Percentage
FoodItemID         int64            8997              0                0.00
RestaurantID       int64            8997              0                0.00
FoodName             str            8997              0                0.00
Category             str            8997              0                0.00
Price              int64            8997              0                0.00
PreparationTime    int64            8997              0                0.00
Calories         float64            8865            132                1.47
Availability         str            8997              0                0.00

---Numeric Summary Statistics---
                  count     mean      std    min     25%     50%     75%  \
FoodItemID       8997.0  4499.00  2597.35    1.0  2250.0  4499.0  6748.0   
RestaurantID     8997.0   601.39   346.24    1.0   302.0   602.0   901.0   
Price            8997.0   177.88    91.65 -358.0   117.0   178.0   238.0   
PreparationTime  8997.0    17.68     7.80    3.0    12.0    17.0    23.0   
Calories         8865.0   400.79   149.23   50.0   302.0   400.0   503.0   

                    max     IQR  Outliers  
FoodItemID       8997.0  4498.0         0  
RestaurantID     1200.0   599.0         0  
Price             503.0   121.0       107  
PreparationTime    48.0    11.0        23  
Calories         1030.0   201.0        38  

---Categorical Summary Statistics---

Value Counts for 'FoodName':
FoodName
Tandoori Roti      371
Butter Naan        345
Garlic Naan        343
Brownie            326
Kulcha             319
                  ... 
masala chai          2
VEG BURGER           2
 Fish Fingers        2
 Masala Chai         1
BIRYANI              1
Name: count, Length: 124, dtype: int64

Value Counts for 'Availability':
Availability
Yes    8060
No      937
Name: count, dtype: int64

Value Counts for 'Category':
Category
Fast Food      1544
Main Course    1539
Desserts       1512
Beverages      1487
Starters       1470
Breads         1445
Name: count, dtype: int64

==================================================

```
## 6. Traffic dataset (traffic.csv)
### Summary of findings
- **Missing Values:** `TrafficLevel` (147 rows)
- **Duplicates:** None
- **Formatting Issues:** `FoodName` has trailing whitespaces and inconsistent upper case strings
- **Invalid Values:** `AverageSpeed` has -ve values (min: -47.7)
- **Datatype Mismatch:** 
    -`Date` & `Time` convert from str to datetime and time format respectively
    -`TrafficID` convert int64 to str to prevent numerical operations
- **Extreme Outliers:** `AverageSpeed` with 299 outliers
### Raw Profiling Output
```text

==================================================
DETAILED PROFILE OF TRAFFIC:
==================================================

---Data Types and Data Completeness---
             DataType  Non-Null Count  Missing Count  Missing Percentage
TrafficID       int64           18335              0                 0.0
City              str           18335              0                 0.0
Date              str           18335              0                 0.0
Time              str           18335              0                 0.0
TrafficLevel      str           18188            147                 0.8
AverageSpeed  float64           18335              0                 0.0

---Numeric Summary Statistics---
                count     mean      std   min     25%     50%      75%  \
TrafficID     18335.0  9168.00  5293.00   1.0  4584.5  9168.0  13751.5   
AverageSpeed  18335.0    23.48    14.34 -47.7    13.9    23.0     32.4   

                  max     IQR  Outliers  
TrafficID     18335.0  9167.0         0  
AverageSpeed    119.9    18.5       299  

---Categorical Summary Statistics---

Value Counts for 'City':
City
Mumbai           759
Jaipur           757
Chennai          756
Ahmedabad        754
Visakhapatnam    752
Nagpur           748
Kolkata          745
Ludhiana         745
Indore           741
Bhopal           740
Bhubaneswar      737
Patna            736
Lucknow          734
Vadodara         733
Kochi            732
Delhi            731
Nashik           730
Raipur           729
Guwahati         726
Bengaluru        717
Coimbatore       712
Hyderabad        711
Chandigarh       704
Pune             703
Surat            703
Name: count, dtype: int64

Value Counts for 'TrafficLevel':
TrafficLevel
Moderate    5656
High        5256
Low         4197
Severe      3079
NaN          147
Name: count, dtype: int64

==================================================
```
## 7. Weather dataset (weather.csv)
### Summary of findings
- **Missing Values:** `City`(91 rows) & `Rainfall`(269 rows)
- **Duplicates:** None
- **Formatting Issues:** None
- **Invalid Values:** 
    -`Humidity` has -ve values (min: -97.0)
    -`Rainfall` has extreme values (max: 1249.3) possible sensor error
    -`Temperature` has extreme values (max: 59.9) exceeding typical regional threshold
- **Datatype Mismatch:** 
    -`Date` convert from str to datetime format
    -`Humidity` convert from int64 to float64 format
    -`WeatherID` convert int64 to str to prevent numerical operations
- **Extreme Outliers:** 
    - `Temperature` with 216 outliers
    - `Rainfall` with 2648 outliers
    - `Humidity` with 315 outliers
### Raw Profiling Output
```text
==================================================
DETAILED PROFILE OF WEATHER:
==================================================

---Data Types and Data Completeness---
                 DataType  Non-Null Count  Missing Count  Missing Percentage
WeatherID           int64           18264              0                0.00
City                  str           18173             91                0.50
Date                  str           18264              0                0.00
Temperature       float64           18264              0                0.00
Rainfall          float64           17995            269                1.47
Humidity            int64           18264              0                0.00
WeatherCondition      str           18264              0                0.00

---Numeric Summary Statistics---
               count     mean      std   min      25%     50%       75%  \
WeatherID    18264.0  9132.50  5272.51   1.0  4566.75  9132.5  13698.25   
Temperature  18264.0    26.80     7.30   5.0    22.00    27.2     31.50   
Rainfall     17995.0    35.85    77.45   0.0     0.00     5.3     29.20   
Humidity     18264.0    58.22    19.12 -97.0    49.00    59.0     69.00   

                 max     IQR  Outliers  
WeatherID    18264.0  9131.5         0  
Temperature     59.9     9.5       216  
Rainfall      1249.3    29.2      2648  
Humidity       100.0    20.0       315  

---Categorical Summary Statistics---

Value Counts for 'City':
City
Indore           754
Kolkata          751
Bengaluru        750
Mumbai           747
Raipur           745
Ludhiana         744
Lucknow          738
Vadodara         738
Visakhapatnam    736
Pune             735
Surat            733
Nashik           733
Bhopal           724
Coimbatore       722
Chennai          721
Ahmedabad        718
Delhi            715
Bhubaneswar      715
Kochi            713
Hyderabad        712
Patna            711
Nagpur           709
Jaipur           705
Chandigarh       703
Guwahati         701
NaN               91
Name: count, dtype: int64

Value Counts for 'WeatherCondition':
WeatherCondition
Clear     6367
Cloudy    3664
Humid     2723
Rainy     2717
Foggy     1873
Stormy     920
Name: count, dtype: int64

==================================================
```
## 8. Cities dataset (cities.csv)
### Summary of findings
- **Missing Values:** `AverageIncome`(2 rows)
- **Duplicates:** None
- **Formatting Issues:** None
- **Invalid Values:** None
- **Datatype Mismatch:** 
    -`CityID` convert int64 to str to prevent numerical operations
- **Extreme Outliers:** 
    - `Population` with 2 outliers
### Raw Profiling Output
```text
==================================================
DETAILED PROFILE OF CITIES:
==================================================

---Data Types and Data Completeness---
              DataType  Non-Null Count  Missing Count  Missing Percentage
CityID           int64              25              0                 0.0
City               str              25              0                 0.0
Population       int64              25              0                 0.0
Region             str              25              0                 0.0
AverageIncome  float64              23              2                 8.0

---Numeric Summary Statistics---
               count        mean         std        min        25%        50%  \
CityID          25.0       13.00        7.36        1.0        7.0       13.0   
Population      25.0  6594987.44  7486161.06  1059078.0  2177335.0  3043446.0   
AverageIncome   23.0  1025811.70   273950.81   650018.0   806232.0   961447.0   

                     75%         max        IQR  Outliers  
CityID              19.0        25.0       12.0         0  
Population     8636140.0  32939024.0  6458805.0         2  
AverageIncome  1232511.0   1609572.0   426279.0         0  

---Categorical Summary Statistics---

Value Counts for 'City':
City
Mumbai           1
Delhi            1
Bengaluru        1
Hyderabad        1
Chennai          1
Kolkata          1
Pune             1
Ahmedabad        1
Jaipur           1
Lucknow          1
Chandigarh       1
Surat            1
Nagpur           1
Indore           1
Bhopal           1
Coimbatore       1
Kochi            1
Visakhapatnam    1
Patna            1
Bhubaneswar      1
Guwahati         1
Nashik           1
Ludhiana         1
Vadodara         1
Raipur           1
Name: count, dtype: int64

Value Counts for 'Region':
Region
West     9
South    6
North    5
East     5
Name: count, dtype: int64

==================================================

```
## 9. Customer Feedback dataset (customer_feedback.csv)
### Summary of findings
- **Missing Values:** `CustomerRating`(294 rows) & `Review`(1058 rows)
- **Duplicates:** None
- **Formatting Issues:** None
- **Invalid Values:** 
    -`DeliveryRating` has (max: 9.0) scale should be between 1.0-5.0
- **Datatype Mismatch:** 
    -`DeliveryRating` & `FoodRating` convert from int64 to float64 format
    -`FeedbackID` and `OrderID` convert int64 to str to prevent numerical operations
- **Extreme Outliers:** None
### Raw Profiling Output
```text
==================================================
DETAILED PROFILE OF CUSTOMER FEEDBACK:
==================================================

---Data Types and Data Completeness---
               DataType  Non-Null Count  Missing Count  Missing Percentage
FeedbackID        int64           14200              0                0.00
OrderID           int64           14200              0                0.00
CustomerRating  float64           13906            294                2.07
DeliveryRating    int64           14200              0                0.00
FoodRating        int64           14200              0                0.00
Review              str           13142           1058                7.45
Sentiment           str           14200              0                0.00

---Numeric Summary Statistics---
                  count       mean      std       min        25%       50%  \
FeedbackID      14200.0    7100.50  4099.33       1.0    3550.75    7100.5   
OrderID         14200.0  110267.52  5910.34  100001.0  105147.75  110283.5   
CustomerRating  13906.0       3.58     1.35       1.0       2.00       4.0   
DeliveryRating  14200.0       3.52     1.40       1.0       2.00       4.0   
FoodRating      14200.0       3.48     1.35       1.0       2.00       4.0   

                      75%       max      IQR  Outliers  
FeedbackID       10650.25   14200.0   7099.5         0  
OrderID         115390.25  120500.0  10242.5         0  
CustomerRating       5.00       5.0      3.0         0  
DeliveryRating       5.00       9.0      3.0         0  
FoodRating           5.00       5.0      3.0         0  

---Categorical Summary Statistics---

Value Counts for 'Review':
Review
Amazing experience overall.                    1294
Packaging was excellent and food was hot.      1287
Best biryani in town!                          1282
Great food and fast delivery!                  1256
Delivery partner was very polite.              1251
Loved the taste, will order again.             1250
NaN                                            1058
Food was okay, nothing special.                 695
Delivery was on time but food was mediocre.     685
Average experience.                             655
Delivery took way too long.                     611
Wrong item delivered.                           606
Quality was not up to the mark.                 575
Order was incomplete.                           571
Food arrived cold and late.                     568
Very disappointed with the service.             556
Name: count, dtype: int64

Value Counts for 'Sentiment':
Sentiment
Positive    7842
Negative    3601
Neutral     2757
Name: count, dtype: int64

==================================================

```
## 10. Order items dataset (order_items.csv)
### Summary of findings
- **Missing Values:** `TotalPrice`(435 rows)
- **Duplicates:** None
- **Formatting Issues:** None
- **Invalid Values:** 
    -`Quantity` has -ve values (min: -4)
- **Datatype Mismatch:** 
    -`UnitPrice` convert from int64 to float64 format
    -`OrderItemID`, `FoodItemID` & `OrderID` convert int64 to str to prevent numerical operations
- **Extreme Outliers:** 
    - `Quantity` with 3340 outliers
    - `UnitPrice` with 147 outliers
    - `TotalPrice` with 2327 outliers
### Raw Profiling Output
```text
==================================================
DETAILED PROFILE OF ORDER ITEMS:
==================================================

---Data Types and Data Completeness---
            DataType  Non-Null Count  Missing Count  Missing Percentage
OrderItemID    int64           42378              0                0.00
OrderID        int64           42378              0                0.00
FoodItemID     int64           42378              0                0.00
Quantity       int64           42378              0                0.00
UnitPrice      int64           42378              0                0.00
TotalPrice   float64           41943            435                1.03

---Numeric Summary Statistics---
               count       mean       std       min        25%       50%  \
OrderItemID  42378.0   21189.50  12233.62       1.0   10595.25   21189.5   
OrderID      42378.0  110250.93   5913.09  100001.0  105122.25  110265.0   
FoodItemID   42378.0    4498.67   2605.66       1.0    2236.00    4483.5   
Quantity     42378.0       1.69      0.99      -4.0       1.00       1.0   
UnitPrice    42378.0     181.72     84.53      40.0     119.00     180.0   
TotalPrice   41943.0     313.14    238.00      40.0     153.00     241.0   

                   75%       max       IQR  Outliers  
OrderItemID   31783.75   42378.0  21188.50         0  
OrderID      115380.00  120500.0  10257.75         0  
FoodItemID     6754.00    8997.0   4518.00         0  
Quantity          2.00       4.0      1.00      3340  
UnitPrice       239.00     503.0    120.00       147  
TotalPrice      406.00    2000.0    253.00      2327  

==================================================
```
## 11. Promotions dataset (promotions.csv)
### Summary of findings
- **Missing Values:** None
- **Duplicates:** None
- **Formatting Issues:** None
- **Invalid Values:** None
- **Datatype Mismatch:** 
    -`StartDate` & `EndDate` convert from str to datetime format
    -`DiscountPercentage` convert from int64 to float64 format
    -`PromotionID` convert int64 to str to prevent numerical operations
- **Extreme Outliers:** None
### Raw Profiling Output
```text
==================================================
DETAILED PROFILE OF PROMOTIONS:
==================================================

---Data Types and Data Completeness---
                   DataType  Non-Null Count  Missing Count  Missing Percentage
PromotionID           int64             300              0                 0.0
CouponCode              str             300              0                 0.0
DiscountPercentage    int64             300              0                 0.0
CampaignName            str             300              0                 0.0
StartDate               str             300              0                 0.0
EndDate                 str             300              0                 0.0

---Numeric Summary Statistics---
                    count    mean    std   min    25%    50%     75%    max  \
PromotionID         300.0  150.50  86.75   1.0  75.75  150.5  225.25  300.0   
DiscountPercentage  300.0   27.67  12.84  10.0  15.00   25.0   40.00   50.0   

                      IQR  Outliers  
PromotionID         149.5         0  
DiscountPercentage   25.0         0  

---Categorical Summary Statistics---

Value Counts for 'CouponCode':
CouponCode
ZOMBCPD6    1
ZOMMMJAQ    1
ZOMDE2A6    1
ZOMTS3XV    1
ZOM6SYNB    1
           ..
ZOMMUY0F    1
ZOMZ1VLS    1
ZOMU4HH3    1
ZOMQ5U50    1
ZOMKA2ZX    1
Name: count, Length: 300, dtype: int64

Value Counts for 'CampaignName':
CampaignName
Mega Cashback Week           31
First Order Free Delivery    28
Summer Splash                27
Late Night Cravings          26
App Exclusive Deal           26
Payday Delight               26
Weekend Bonanza              26
Festive Feast                26
Great Indian Food Fest       23
New User Special             21
Monsoon Munchies             21
Republic Day Offer           19
Name: count, dtype: int64

==================================================
```
## 12. Payments dataset (payments.csv)
### Summary of findings
- **Missing Values:** `TransactionID`(183 rows)
- **Duplicates:** None
- **Formatting Issues:** None
- **Invalid Values:** None
- **Datatype Mismatch:** 
    -`PaymentDate` convert from str to datetime format
    -`PaymentID` & `OrderID` convert int64 to str to prevent numerical operations
- **Extreme Outliers:** None
### Raw Profiling Output
```text
==================================================
DETAILED PROFILE OF PAYMENTS:
==================================================

---Data Types and Data Completeness---
              DataType  Non-Null Count  Missing Count  Missing Percentage
PaymentID        int64           20493              0                0.00
OrderID          int64           20493              0                0.00
PaymentMethod      str           20493              0                0.00
PaymentStatus      str           20493              0                0.00
TransactionID      str           20310            183                0.89
PaymentDate        str           20493              0                0.00

---Numeric Summary Statistics---
             count       mean      std       min       25%       50%  \
PaymentID  20493.0   10247.00  5915.96       1.0    5124.0   10247.0   
OrderID    20493.0  110254.44  5916.11  100001.0  105130.0  110258.0   

                75%       max      IQR  Outliers  
PaymentID   15370.0   20493.0  10246.0         0  
OrderID    115385.0  120500.0  10255.0         0  

---Categorical Summary Statistics---

Value Counts for 'PaymentMethod':
PaymentMethod
Debit Card          3529
Net Banking         3467
Cash on Delivery    3457
UPI                 3361
Credit Card         3349
Wallet              3330
Name: count, dtype: int64

Value Counts for 'PaymentStatus':
PaymentStatus
Success     16372
Failed       1659
Refunded     1641
Pending       821
Name: count, dtype: int64

==================================================
```


