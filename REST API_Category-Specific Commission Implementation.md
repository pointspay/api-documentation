# Pointspay

### **Appendix 1: Category-Specific Commission Implementation**

This appendix details the implementation for merchants who require category-specific commission calculations. This functionality is optional and should only be utilized if the commission rates for different product categories vary.

______ 

**1. Applicability**

- **When to Implement:** This category-specific implementation is required only if the commission for different categories is different. Large merchants with diverse product catalogs and varied commission structures across these categories will find this appendix relevant.
- **When to Skip:** If a fixed commission rate applies across all product categories, then this category-specific implementation should be entirely skipped.

-------

**2. Data Transmission Requirement**

For merchants implementing category-specific commissions, with each payment request, under `additional data`, the merchant must pass a list of product category codes along with the sum of the cart amount for each respective category. The category codes themselves will be provided by the Pointspay team.

------

**3. Parameter Details for Category Data**

The following parameters are used to specify category-specific amounts within the `categories` array:

| Parameter | Type   | Mandatory | Description                                                                                                                                                                                                                                        |
| --------- | ------ | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| amount    | String | No        |- The category-specific amount in minor units. <br>- Maximum 10 characters.<br>- E.g., For a category amount of USD 100.00, the value passed should be `10000` .|
| code      | String | No        | This is the category code. It is crucial that the category code is unique for each category.                                                                                                                                                       |

-----

**4. Implementation Example**

Consider a scenario where a merchant has two distinct product categories: "Fashion" and "Electronics". The Pointspay team has provided the following respective category codes: `FASHION` and `ELECTRO`.

If the sum of fashion category products in the cart is USD 180.00 and the sum of electronics category products in the cart is USD 515.00, the parameters and values should be passed within the `categories` array as follows:

```
"categories”: [
  {"amount":"18000","code":"FASHION"},
  {"amount":"51500","code":"ELECTRO"}
]
```

**Important Note:** If the cart contains products from only one category, then only that specific category should be included within the `categories` array.

-----

**5. Base Categories**

Below is the list of base categories. The Pointspay team will help configure them based on the merchant's needs.  
Please consult the Pointspay integration team—they will assist with the appropriate category codes for integration.

| Category Name   | Category Code | Description                                          |
| --------------- | ------------- | ---------------------------------------------------- |
| Redemption Only | REDEMPTION    | Redemption Only                                      |
| Standard        | STANDARD      | Standard, Redeem and Earn                            |
| Diamonds        | DIAMONDS      | Diamonds and Jewellery                               |
| Perfumes        | PERFUMES      | Perfumes                                             |
| ACTIVITIES      | ACTIVITIES    | Travel activities                                    |
| Accessories     | ACCESSOR      | Electronics accessories                              |
| Car Rentals     | CAR           | Car Rentals                                          |
| Hotels          | HOTELS        | Hotels                                               |
| Flights         | FLIGHT        | Flights                                              |
| Household       | HOUSE         | Household                                            |
| Games           | GAMES         | Games                                                |
| Experiences     | EXPER         | Experiences                                          |
| Gifts           | GIFTS         | Gifts                                                |
| Fashion         | FASHION       | Fashion                                              |
| Toys            | TOYS          | Toys                                                 |
| Computers       | COMP          | Computers                                            |
| Mobiles         | MOBILES       | Mobiles                                              |
| Electronics     | ELECTRO       | Electronics                                          |
| Books           | BOOKS         | Books                                                |
| Products        | PRODUCTS      | Default, general-purpose category used for merchants |
