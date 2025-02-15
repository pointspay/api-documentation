# API Documentation

## Extracted Text

User manual for Shopify integration
Installing Pointspay application......................................................................................................3
Dashboard page............................................................................................................................ 6
Configuration page........................................................................................................................ 7
Checkout........................................................................................................................................8
Refund......................................................................................................................................... 11
Installing Pointspay application
Merchants can install Pointspay payment applications by navigating to Settings > Payments in
their store and adding a new payment method.
Then, in the list of payment methods, they can search for Pointspay and select one or more
available options.
Then, they can choose the provider offering that payment method.
Once on the selected payment provider page, they can click the “Install” button to start the
installation process.
This will prompt them to confirm permissions and add this payment method to their Shopify
payments settings.
After confirming permissions and installing the integration, merchants will be redirected to the
Pointspay Configuration page.
Dashboard page
After successfully installing a given Pointspay payment flavor, merchants can access its
dashboard page by navigating to Settings > Payments in their store and selecting that payment
method. This will open up the standard Shopify dashboard page for that payment method.
From this section, merchants can:
●
Enable or disable this payment option on the storefront
●
Toggle test mode to switch between the test and live environments and credentials for
the Pointspay API
●
Click "Manage" to navigate to the Pointspay Integration configuration page
Configuration page
Merchants must enter the shop code used for payment requests, along with the consumer key
and the Pointspay certificate provided for both test and live environments.
Additionally, integration will generate a certificate public/private key pair after the credentials are
saved and show the private key as a read-only field, with only the last four characters displayed
to the user.
Finally, merchants can download the .p12 certificate file to share with the Pointspay team and
process payment requests from Shopify.
Checkout
Each enabled Pointspay payment flavor will be displayed as a standard payment method
offered in the Shopify checkout during the payment step of the checkout process.
After the customer selects a Pointspay payment flavor and submits an order, the integration will
redirect the customer to the Pointspay portal, where she/he can finalize or cancel the payment.
In case the payment is successful on the Pointspay portal, the customer is redirected to the
Thank you page:
In case of a payment error or cancellation on the Pointspay portal, the customer is redirected
back to the checkout page:
Refund
Merchants can refund a paid order by clicking the “Refund” button on the order details page.
This will open a separate page where the merchant can select which order items or amounts
they want to refund. In any case, that will result in an accumulated refund amount that cannot be
greater than the remaining paid amount that still has not been refunded (in the case where there
haven’t been any refunds on the order yet, the refundable amount will be equal to the total order
amount).


## Extracted Images

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_1_5.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_3_17.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_4_22.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_4_23.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_5_27.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_6_31.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_7_35.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_8_39.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_9_42.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_10_46.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_11_50.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_12_54.png)

