# User manual
### Pointspay - BigCommerce application
**Application installation ** 
**Configuration page ** 
**Checkout ** 
**Refund ** 
**Application uninstallation ** 
### Application installation
By going to **Apps > Marketplace,** merchant goes on the BigCommerce marketplace where
he/she can search for a Pointspay application.
Then, merchants should be able to search and then install the Pointspay integration as a
BigCommerce application from the BigCommerce marketplace.

---

When merchant click on “ Get this app ” button, he/she should be redirected to the marketplace
app page:
When the app is installed, its configuration page should be displayed to a merchant and the
menu item should appear in Apps section .

---

### Configuration page
The configuration page can be opened from the My Apps page by clicking “ Launch ” button for
the Pointspay application, but also from side menu in the Apps section by clicking Pointspay
menu item.
Application’s configuration page has three tabs:
● Authorization - Authorization is required to be able to configure payment flavors and
change general setting
● General settings - Settings common to all payment flavors and order status mapping
● Payment flavours - Connection and other settings for each payment flavor
If the merchant is not authorized, he/she only has access to the Authorization tab on the page,
while the remaining two tabs are unavailable.
### Authorization
The merchant needs to select the environment and enter the API key to fetch Pointspay
payment methods and configure them.
If the API key is valid and the authorization is successful, the merchant will see a message
confirming successful authorization. Two additional tabs ( General settings and Payment
flavours ) become available on the configuration page.

---

### General settings
The general settings tab contains options common to all Pointspay payment methods. In this
form, the merchant can choose to enable or disable Debug mode, which logs to the server
every request and response to the Pointspay API if debug mode is enabled.
The other option allows the merchant to define the order status that should be assigned to the
BigCommerce order when the order is placed using a Pointspay payment method. The list of
order statuses in BigCommerce is fixed, but the merchant can change order status labels by
navigating to “ Orders → Order Statuses ”. However, all available statuses are listed with the
default status being “ Awaiting fulfillment ”.

---

### Payment flavours
In the payment flavours tab, the retrieved available methods are displayed as items, where each
payment flavour can be individually configured.
The merchant can enable or disable a method, select countries in which the method will be
available, and set a sort order number to define the order in which the payment methods appear
at checkout. To configure the method, a merchant must enter the shop code used for payment
requests, along with the consumer key and the Pointspay certificate.

---

After the credentials are saved, integration will generate a certificate public/private key pair and
show the private key as a read-only field, with only the last four characters displayed to the user.
Finally, merchants can download the **.** **cer** certificate file to share with the Pointspay team and
process payment requests from the BigCommerce.
### Checkout
Each enabled Pointspay payment flavor will be displayed as a standard payment method offered
in the BigCommerce checkout during the payment step of the checkout process.
A payment method appears at checkout if it is enabled on the configuration page and if the
customer's billing address country is among the countries where the flavour is available.
Pointspay payment methods are displayed in the order defined by the Sort order values in the
flavours configurations.
If the customer has other payment methods available besides the Pointspay payment methods
(such as Cash on Delivery), those will be listed before the Pointspay methods. Pointspay
payment methods appearing afterward in the order defined on the configuration page.

---

After the customer selects a Pointspay payment flavor and submits an order, the integration will
redirect the customer to the payment page, where she/he can finalize or cancel the payment.
In case the payment is successful, the customer is redirected to the Thank You page.
In case of a payment error or cancellation on the payment page, the customer is redirected back
to the payment step of the checkout page. Also, a customer is shown a message why he was
returned to checkout page.

---

### Refund
Merchant can refund a paid order by clicking on the Refund menu item on the selected order on
the order details page. Than, merchant has several refund options:
1. Refund individual items: In this way, a merchant needs to manually choose refund
quantity for each item
2. Refund entire order/Refund all remaining items: In this way, the merchant will refund all
(remaining) items
3. Refund specific order amount: In this way, the merchant could enter the refund amount,
without associating the refund with a specific order item.

---

When merchant clicks on the Continue button, a next page opens that he/she chooses refund
method and gives optional refund reason.
The Pointspay application handles only methods that don’t have Store Credit method and in that
case try to create refund on the Pointspay. This is because, in the case of a Store Credit refund,
the order is refunded, but the payment is not since the customer receives credits that can be
used as a discount in a future purchase.

---

### Rejecting refund
Since it is not possible to reject a refund action or delete a created refund on the BigCommerce
if the refund is not possible or not successful on the Pointspay side, in that case application logs
a warning that the change was declined and the reason, if available.
Apart from the logs on the server, the merchant can see that refund is declined and the reason
on the order details page as order comments section. Despite an order comment, the status of
the order itself is still refund (or partial refund) as if refund request passed successfully.
### Application uninstallation
If the merchant wants to uninstall the application, he/she needs to find apps among My Apps
application or on the BigCommerce marketplace. Then, merchant should click on the “ Uninstall ”
button. Uninstall action removes all configuration and other data for this merchant from the
database.

---