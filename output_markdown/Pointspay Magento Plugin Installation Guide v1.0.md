www.pointspay.com

# Pointspay

# Magento 2 Plugin Installation Guide

---

www.pointspay.com

## 1 ## Introduction

Pointspay is an Alternative Payment Method (APM) that lets shoppers pay with their

favourite loyalty program miles or points at participating web shops.

The Pointspay plugin for Magento 2 enables merchants who are on Magento 2 to easily

install Pointspay as an additional payment method at their checkout and process

payments and refunds seamlessly.

With a single installation of the Pointspay plugin merchants have the ability to enable one

or more of the available Pointspay payment method variants, like Pointspay & Flying

Blue+.

## 2 ## Supported Magento Versions

The Pointspay Magento plugin is compatible with 2.2.x, 2.3.x & 2.4.x Magento versions. The

plugin has been certified for versions up to 2.4.6.

## 3 ## Installation Details

•

Execute the following command for installing versions 2.4.x or 2.3.x of the Pointspay

plugin via Composer:

composer require pointspay/pointspay-magento

•

Execute the following command for installing version 2.2.x version of the plugin via

Composer:

composer require pointspay/pointspay-magento-2.2

## 4 ## Plugin Configurations

Navigate to Pointspay payment method via Magento Admin -> Stores -> Settings ->

Configuration -> Sales -> Payment Methods -> Pointspay to configure the plugin.

**Note:** Refer Image 1 below that shows the “Payment Methods” screen after Pointspay

plugin installation.

---

www.pointspay.com

Image 1

4.1 Fetch available Pointspay payment method variants

The plugin comes pre-packaged with Pointspay as the default payment method.

Additional variants (Flying Blue+ for instance) can be added on the fly by synchronizing

the plugin against the Pointspay server. New variants that are added on the Pointspay

platform from time to time can hence be added and enabled for the web shop without

additional plugin installations.

Image 2

**Configuration**

**Mandatory**

**Description**

**API key**

Yes

•

Provided by Pointspay during onboarding.

•

Authorizes and authenticates the fetching of

available variants of Pointspay payment method.

---

www.pointspay.com

**Note:** Please remember to save the API key config prior

to fetching available payment methods.

4.2 Basic Settings

Configure the following basic settings for every Pointspay payment method variant that

should be enabled.

Image 3

**Configuration**

**Mandatory**

**Description**

**Enabled**

Yes

Select “Yes” to list the payment method on the

merchant’s checkout page.

**Environment**

Yes

When “Sandbox” is selected, payment requests are

sent to Pointspay’s staging environment. Else, to

Pointspay’s live environment.

**Shop code**

Yes

Provided by Pointspay during onboarding.

**Debug**

Yes

Select “Yes” to enable logging in Pointspay-specific

log flies.

**Payment from**

**applicable**

**countries**

Yes

Select “All Allowed Countries” to enable the payment

method for all countries allowed for each payment

method variant. For example, France & The

Netherlands for Flying Blue+. To enable the payment

method variant for just some of the allowed countries,

please select the option “Specific Countries”.

**Note:**

---

www.pointspay.com

•

For physical goods, the billing country of the

registered user is validated against the enabled

countries.

o

In case of a guest shopper, the shipping

country is considered instead.

•

In case of virtual goods, the merchant country is

considered.

**Payment from**

**specific**

**countries**

No

When “Specific Countries” option is selected, select

one or more countries from the list.

**Sort order**

Yes

Defines the sequence of the payment method listing

on the merchant’s checkout page.

**Cancel URL**

No

Shoppers would be redirected to this URL upon

payment cancellation if configured.

4.3 Access Settings

Configure the following access settings for every Pointspay payment method variant that

should be enabled.

**Note:** Always configure access settings in “Website scope”.

Image 4

---

www.pointspay.com

Image 5

**Configuration**

**Mandatory**

**Description**

**Consumer key**

Yes

Provided by Pointspay during onboarding.

**Pointspay**

**certificate**

Yes

This is a .p12 digital certificate file that shall be provided

by Pointspay during onboarding.

**Merchant**

**certificate**

Yes

This is a .p12 digital certificate file that should be

downloaded and shared with the Pointspay team for

uploading it against the merchant’s account at

Pointspay.

**Note:** Please flush the Cache Storage every time the configuration settings are saved.

---

www.pointspay.com

Image 6

## 5 ## Refunds

Pointspay Refunds are integrated with Magento’s Online Refund feature under Credit

Memo.

1.

Navigate to Sales -> Orders -> View the order -> Select Invoices -> Navigate to the

invoice details by clicking the “View” link -> Click on “Credit Memo” (on top-right).

2. Select the amount to be refunded under Shipping.

3. In case of partial refunds, click the “Update Totals” for recalculation.

4. Click on “Refund” to initiate full or partial refund.

Image 7

---

