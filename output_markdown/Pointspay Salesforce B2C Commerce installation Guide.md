![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage1.png)

Integration user manual

Salesforce B2C Commerce integration


Installation and setup

Installation

Step 1: Add cartridge to cartridge path

Upload the cartridge poinstpay\_sfra into your sandbox updating the cartridge path. To do so, go to **Business Manager > Administration > Sites > Manage Sites > Your Target Site > Settings** and insert pointspay\_sfra before your cartridges record. Please also make sure to include the app\_storefront\_base cartridge which is the root SFCC cartridge required for all others to work.

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage2.png)

Click apply and verify that the pointspay\_sfra cartridge is displayed in the Effective Cartridge Path.

<a name="_page2_x72.00_y506.77"></a>Step 2: Import metadata archive

Upload and import pointspayMetadata.zip from the cartridge metadata folder, which includes definitions for payment providers, methods and custom configurations. To do so, go to **Business Manager >Administration > Site Development > Site Import & Export.** Upload archive using Local option in the Upload Archive section. Make sure to change the name of the “RefArch” folder to the name of the site you want to upload this to. After upload choose pointspayMetadata.zip in the list and click on the Import button.

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage3.png)

Make sure to verify the status of the import once it completes.

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage4.png)

<a name="_page3_x72.00_y339.70"></a>Payment flavor configuration

After successfully adding the cartridge to the cartridge path and uploading the metadata files, available Pointspay payment flavors will be shown in the list of payment methods, available at **Business Manager > Merchant Tools > Ordering > Payment Methods.**

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage5.png)From here, you can configure the native Salesforce configuration options, such as name, description, supported countries, currencies and customer groups for each of the Pointspay payment flavors, as well as define some amount conditions for which you want to display these flavors for.

In addition to that, there are also custom Pointspay configurations that are required in order to display these flavors on the Salesforce B2C storefront. These are available within the “Pointspay” section of the payment method configuration page.

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage6.png)

Pointspay configuration consists of the following environment-specific fields:

- **Shop code** - text field
- **Consumer key** - text field
- **Private key** - textarea field (value used for signing payment requests to the Pointspay API)
- **Pointspay public key** - textarea field (value used for verifying incoming requests from the Pointspay API)
- **Debug mode** - toggle field where merchants can select whether to switch the debug mode on or off

<a name="_page4_x72.00_y522.12"></a>Displaying payment flavors on the storefront

After configuring the Pointspay payment flavors, once customers add products to their cart and enter their shipping and billing information, they will be presented with Pointspay payment flavors among available payment options in the billing section of the checkout page.

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage7.png)

Once the customer selects a Pointspay payment flavor by clicking on its corresponding tab, he/she will be presented with its title and description from the configuration.

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage8.png)

<a name="_page7_x72.00_y72.00"></a>Order submission

After confirming their selection, customers reach the final step before placing their order where they can review all of the entered information and selected shipping and billing methods, and can choose to edit their cart before placing the order.

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage9.png)

After hitting the “Place Order” button, customers are redirected to an externally hosted payment page to complete their payment.

In the case of Flying Blue+, here they can choose whether to pay for the order with a credit card or accumulated loyalty points (or a combination of those two).

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage10.png)

After confirming and paying for the order, customers are redirected back to the Salesforce B2C storefront and presented with the order confirmation page, where they can once again see the order summary with all the information and selected shipping and payment options.

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage11.png)

<a name="_page10_x72.00_y72.00"></a>Order management

After an order paid using one of Pointspay payment flavors has been created, merchants can review it by going to **Business Manager > Merchant Tools > Ordering > Orders** and searching for it by its ID.

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage12.png)

On the payment tab, they can review the current status of the payment, as well as the selected payment flavor and amount.

![](../output_images/PointspaySalesforceB2C_CommerceInstallationGuideImages/SalesforceB2C_CommerceInstallationImage13.png)

