# API Documentation

## Extracted Text

Page 1 of 10 
  
 
 
 
 
 
 
 
 
 
 
 
 
 
 
Pointspay 
WooCommerce Plugin Installation Guide  
Version 1.3 
 
 
 
 
 
 
 
Page 2 of 10 
  
 
1 Introduction 
Pointspay is an Alternative Payment Method (APM) that lets shoppers pay with their favourite 
loyalty program miles or points at participating web shops. 
The Pointspay plugin for WooCommerce enables merchants who are on WooCommerce to easily 
install Pointspay as an additional payment method at their checkout and process payments and 
refunds seamlessly.  
With the Pointspay plugin merchants have the ability to enable one available Pointspay payment 
method variants, like Flying Blue+ or Etihad GuestPay. At the moment multiple variants 
simultaneously are not supported. 
2 Installation 
The Pointspay Woocommerce  plugin is compatible with WordPress Version: 4.0 and 
WooCommerce Version: 3.7 
Automatic installation 
 
Automatic installation is the easiest option as WordPress handles the file transfers itself and you 
don’t need to leave your web browser. To do an automatic install of our plugin, log in to your 
WordPress dashboard, navigate to the Plugins menu and click Add New. You will see Add Plugins 
screen. 
In the search field type “PointsPay for WooCommerce”. Once you’ve found our plugin you can view 
details about it such as the version, rating and description. Most importantly of course, you can 
install it by simply clicking Install Now. 
 
Manual installation 
 
 
 
For installing the plugin manually, you have two options: 
1. 
Extract the plugin zip file and drop its contents in the /wp-content/plugins/ directory of 
your WordPress installation. 
Page 3 of 10 
  
 
2. Navigate to the Plugins menu and click Add New. Click on Upload Plugin button on Add 
Plugins screen. Now, either Browse the plugin zip or drag-and-drop it in the file upload 
container box. Then click on Install Now. 
Plugin activation 
 
 
Once the plugin is installed, you can activate the plugin by clicking on Activate link below the 
plugin name, in Plugins listing. 
 
 
 
3 Plugin Configurations 
After activating the plugin, Configure link will appear below the plugin name in Plugins listing. You 
can click on this link to reach the plugin configuration settings. Alternatively, you can go to 
WooCommerce menu, and click on Settings; then go to Payments tab, and click on Manage 
button next to PointsPay method to reach this page. 
 
NOTE – Please convey the IPN URL listed on settings page to PointsPay team, as they would need to 
configure it at backend for your PointsPay account. 
 
Please note that only one version of the available variants of Pointspay can be used at the same 
time. The available variants are: 
• 
Flying Blue+ 
• 
Etihad GuestPay 
• 
PointsPay 
 
 
 
Basic settings 
Please note the below example relates to configuring Flying Blue+ 
 
Page 4 of 10 
  
 
 
 
Basic Settings relate to usability and display configuration of the payment gateway. The 
options under Basic Settings are as below: 
1. 
Enable / Disable – Use this option to enable or disable PointsPay Payment 
Gateway on your WooCommerce store. 
2. Test Mode – Enable this option if you want to test the payment gateway without 
charging any amount to the customers. Remember that orders will still be placed, 
so use this method only on your test/staging site, and not on live/production site. 
If you enable Test Mode, remember to use test credentials in Access Settings 
fields. 
3. Title – This is the payment method title that customers see during the checkout. 
You can change it to a different relevant text such as “Flying Blue+”. 
4. Description – This is the description for payment method that customers see 
during the checkout. You can change it to a different relevant text “Spend or 
collect Flying Blue miles”. 
5. Cancel URL – This is an optional field in which you can specify the URL to redirect 
the user to if they cancel the payment on PointsPay. By default, the user is 
redirected to order payment page in case of payment cancellation. 
 
To configure Etihad GuestPay instead of Flying Blue+ please use the following parameters 
instead: 
1. 
Title – This is the payment method title that customers see during the checkout. 
You can change it to a different relevant text such as “Etihad GuestPay”. 
Page 5 of 10 
  
 
2. Description – This is the description for payment method that customers see 
during the checkout. You can change it to a different relevant text “Spend or 
collect Etihad Guest points”. 
 
 
 
Access settings 
Access Settings pertain to the access and security configuration of the plugin.  
The options under Access Settings are as below: 
1. 
API Username – API Username is generated at the time of activation of your 
account and helps to uniquely identify your account to PointsPay. 
2. API Password – API Password is generated at the time of activation of your 
account and helps to validate your API Username. 
3. API Access Token – API Access Token is like a secret key that helps to validate 
transaction status notifications from PointsPay to your store. 
4. Merchant Code (Shop ID) – Merchant Code is the unique identity of this 
WooCommerce store, as associated with your account with PointsPay. You will 
have one Merchant Code for each WooCommerce store associated with your 
account on PointsPay. 
5. Private Key – Private Key is used for signing all transaction requests sent from 
your WooCommerce store to PointsPay. A method for generating a set of Private 
and Public keys is described next. 
NOTE – Click on Save changes button after making any changes to PointsPay settings, for 
changes to take effect. 
 
Generating Private and Public Keys 
In order to securely transact with PointsPay, all transaction requests are required to be 
digitally signed. For this purpose, you need to generate a private-public key pair on your 
server, and obtain a certificate corresponding to public key. We recommend to use an 
8192-bit key to accommodate the payload size. Certificate can be either self-signed or 
signed by Certificate Authority (CA). 
You can generate a self-signed certificate using below openssl command: 
 
This plugin assumes that the generated key has no password and SHA256 encryption has 
been used. The above command complies to both the assumptions. 
openssl req -newkey rsa:8192 -nodes -keyout key.pem -x509 -days 
1095 -out 
Page 6 of 10 
  
 
Once you’ve generated the keypair as above, submit  certificctee.cer file to PointsPay to 
associate with your merchant code, whereas copy the contents of keye.pem file in 
Private Key input box under Access Settings. 
 
 
Position among Payment Methods on Checkout Page 
You can change the order of payment methods on Checkout Page by changing their 
order on 
Payments tab under WooCommerce > Settings. 
 
 
 
 
You can click Up and Down arrows to move the payment methods above or below 
another payment method. Alternatively, you can drag and drop the payment 
method at any position after grabbing it by the list icon on the left. 
Once you’ve arranged the payment methods in desired order, click on Save 
changes button for the new order to reflect on your store’s Checkout page. 
Accessing log files 
Page 7 of 10 
  
 
In case you are facing any issues with the plugin, you would want to contact our 
support team for help. In such cases, you should submit log files along with your 
support request. Log  files  are generated for the plugin on daily basis, and can be 
accessed by going to WooCommerce menu and clicking on Status link, and then 
going to Logs tab. 
Select the log file for a particular day for our plugin by selecting it from the 
dropdown menu on the right, and click on View button. Names for all the log files 
for our plugin will begin with ‘pointspay-’. Log file for a specific day will have the 
date in YYYY-MM-DD format in the log file name. 
You can also access today’s log file by clicking on Today’s Logs link under the plugin 
name in plugins 
listing. 
 
Multi – currency plugin compatibility 
This plugin relies on WooCommerce’s get_currency() method. As most multi-currency 
plugins override this method to setup the transaction currency, this plugin should be 
compatible with most such plugins out of the box. Our customers have found this plugin 
to be compatible with the following multi-currency plugins: 
• 
CURCY – WooCommerce Multi Currency by VillaTheme 
• 
WOOCS – Currency Switcher for WooCommerce by realmag777 
 


## Extracted Images

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_1_10.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_2_10.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_2_29.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_2_30.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_3_10.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_3_37.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_4_10.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_4_42.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_5_10.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_6_10.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_6_50.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_7_10.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_7_60.png)

![Image](C:\Users\DanishAnsari_vo4m0y3\ConvertToMDProject\api-documentation\img\image_7_61.png)

