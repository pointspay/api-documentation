![image](https://github.com/user-attachments/assets/aff9c589-000d-4898-bc1e-11d67e1ed574)

# **Pointspay**

REST API Reference 

## 1. Introduction

The target audience of this document is Online Merchants who intend to offer Pointspay as an Alternative Payment Method in their checkout process. The purpose of this document is to guide merchant and partner integrations with the Pointspay REST API.


## 2. Overview

The Pointspay APIs are organized around REST principles. Data objects are represented in JSON.

### 2.1. Environments

Live and sandbox environments are available. The endpoints for the two environments are as below:

| **Environment** | **Endpoint** |
| :- | :- |
| Sandbox | https://uat-secure.pointspay.com |
| Live | https://secure.pointspay.com |

_Table 1_

You can use your sandbox  credentials for authentication on the sandbox endpoint. All transactions made on the sandbox endpoint do not reach live payment networks and program providers. Once you are ready to move to the live environment you can update the endpoint to the live environment 

Endpoint URI: is created by appending the API URI to the environment-specific endpoint (Table 1). 

e.g., https://secure.pointspay.com/api/v1/payments 

### 2.2. OAuth Security

The API’s will be secured with OAuth 1.0a. OAuth is a protocol originally published in the [RFC-5489](https://datatracker.ietf.org/doc/html/rfc5849) and used for securing access to API.

We would be using OAuth 1.0a in its simplest form. This implementation involves one single step, in which we rely on OAuth signatures for server-to-server authentication.

![image](https://github.com/user-attachments/assets/e9a90364-95a0-4ec1-a046-e102a6b74a62)

### 2.3. Generate certificates to digitally sign the transaction

Follow the below process to generate the keypair to sign the transaction request digitally.

- Generate a private-public key pair and obtain a certificate corresponding to the public certificate. We recommend using an 8192-bit key to accommodate the payload size.
- The certificate can be either self-signed or signed by a Certificate Authority (CA). Commands for self-signed certificate generation using openssl command:

| **Open SSL Commands** |
| :- |
| -- Generate private certificate<br>`openssl req -newkey rsa:8192 -nodes -keyout key.pem -x509 -days 1095 -out certificate.cer -sha256` |

Alternatively, the below Java keytool command can be also used:

| **Generate a private/public key pair** |
| :- |
| `keytool -genkeypair -alias  <<your alias>>  -keys -keyalg RSA -keysize 8192 -dname "CN=<<Name>>" -validity 1095 -storetype PKCS12 -keystore <<KeyStore Name>> -storepass  <<your password>>`<br>e.g.<br>`keytool -genkeypair -alias prod-merchant-signature-keys -keyalg RSA -keysize 8192 -dname </p><p>“CN=prod-merchant” -validity 1095 -storetype PKCS12 -keystore prod-merchant-signature- keys.p12  -storepass 12345` |

| **Export the public certificate from a p12/pfx file** |
| :- |
| `keytool -exportcert -alias <<your alias>>  -keys -storetype PKCS12 -keystore <<your alias >>.p12 -file <<CertificateName>>.cer -rfc -storepass <<your password>>`<br>e.g.<br>`keytool -exportcert -alias prod-merchant-signature-keys -storetype PKCS12 -keystore prod-merchant-signature-keys.p12 -file prod-merchant-public-certificate.cer -rfc -storepass 12345` |

1. Share the public certificate (.cer) file with Pointspay which will be added in the trust store at Pointspay side.
2. The pem private key file should not be shared with anyone; it should be known only to the merchant.

### 2.4. Import public certificate to verify the response signature

During  merchant  on-boarding  Pointspay  will  also  share  a  public  certificate  with  the merchant. The merchant can import this certificate in the keystore and use this certificate to verify the response body and signature.

Command to import the public certificate in the merchant’s keystore file: 

`keytool -import -trustcacerts -alias <<your alias>> -file <<public certificate file path>>-keystore <<merchant keystore path>>`<br>e.g.<br>`keytool -import -trustcacerts -alias pointspay -file pointspayPublicCertificate.cer -keystore merchant.keystore`


## 3. Payments

### 3.1. Dynamic Pointspay Logo

Pointspay uses a dynamic payment logo. Hence, it is necessary to use the Pointspay dynamic logo URL for while displaying Pointspay as a payment method.

**Sample code**:

Sandbox:  

`<img id=”ppc_checkout_btn_img” alt=”Pointspay” src=”https://uat-secure.pointspay.com/checkout/user/btn-img-v2?shop_code=njjs8f2aNlqO“>`

`<img id=”ppc_payment_btn_img” alt=”FlyingBluePlus” src=”https://uat-secure.pointspay.com/checkout/user/btn-img-v2?shop_code=5fgs8sdfhqF“>`

Live:  

`<img id=”ppc_checkout_btn_img” alt=”Pointspay” src=”https://secure.pointspay.com/checkout/user/btn-img-v2?shop_code =5I0OHYlLpGAW“>`

`<img id=”ppc_payment_btn_img” alt=”FlyingBluePlus“ src=”https://secure.pointspay.com/checkout/user/btn-img-v2?shop_code =KIJ6JYl0p86N“>`

Pointspay logo URL takes the following parameters:

| **Parameter** | **Mandatory** | **Description** |
| :- | :- | :- |
| `shop_code` | Y | - Shop code provided during merchant onboarding.<br>- Max 32 characters. |
| `language` | N | - Used to display language-specific logo.<br>- 2-character ISO 639-1 language code.<br>- Default language is: en. |

_Table 2_ 

### 3.2. Payments API

This API will initiate the Pointspay payment and create and persist the transaction details in the Pointspay system. This API returns the Pointspay payment URL and the generated payment id in the response.

The API is secured via OAuth which requires adding OAuth headers and a signature to the request and the response needs to be verified accordingly. Please refer Section 5 below for the details on request-response signatures.

| API URI | /api/v1/payments |
| :- | :- |
| HTTP Method | POST |

_Table 3_ 

**Request:** 

| **Parameter** | **Type** | **Mandatory** | **Description** |
| :- | :- | :- | :- |
| `shop_code` | string | Y | - Shop code provided during merchant onboarding.<br>- Max 32 characters. |
| `order_id` | string | Y | - The order id created by merchant.<br>- Max 32 characters.<br>- Allowed characters: [0-1A-Za-z]. |
| `amount` | string | Y | - The payment amount in minor units.<br>- Max 11 characters.<br>- E.g., For a payment amount of USD 100.00, pass value as 10000. |
| `currency` | string | Y | - The currency must be same as displayed to the shopper as basket currency.<br>- 3-character ISO 4217 currency code. |
| `language` | string | N | - The language in which the Pointspay payment pages shall be rendered.<br>- 2-character ISO 639-1 language code.<br>- Default language is: en. |
| `additional_data` | object | N | - An optional additional information can be passed as part of the request.<br>- Please refer section 6. |

_Table 4_

**Response:** 

| **Parameter** | **Type** | **Description** |
| :- | :- | :- |
| `created_at` | string | The Epoch time with milliseconds when the payment transaction was created.<br>e.g. 1694068168722 |
| `href` | string | Payment redirection URL of the Pointspay payment page when the transaction status is ACCEPTED. |
| `order_id` | string | Order id sent by merchant in the request. |
| `payment_id` | string | Unique identifier of the payment transaction in Pointspay. |
| `status` | string | The transaction can be in one of the pre-defined statuses: REJECTED, ACCEPTED or FRAUD. You should redirect a shopper to the Pointspay payment page only when a transaction is in *ACCEPTED* status. |
| `status_message` | string | A more detailed message about the status. |

_Table 5_

### 3.3. Redirect shopper to the Pointspay payment application

Pointspay returns a redirection URI in the response of the Payment API in the href field (Refer Table 5). Before redirecting the shopper to the Pointspay payment application though, the merchant should verify the following points: 

- The payment response status is ACCEPTED.
- The order id in the payment response matches the order on your end.

### 3.4. Pointspay redirection back to the merchant web shop

Once the payment is successful, the shopper would be redirected back to your web shop via the return URL specified by you during merchant onboarding, or the dynamic URLs specified in the payment request. 

You need to provide 3 redirect URLs during onboarding: 

1. **Success link:** The URL to which the shopper would be redirected when the payment is successful.
2. **Cancel link:** The URL to which the shopper would be redirected if he decides to pay with another payment option.
3. **Failure link:** The URL to which the shopper would be redirected when the payment fails.

All these links can be the same, depending on your application logic. They will all have the following request body parameters submitted by Pointspay while redirection, Pointspay will do HTTP POST form submission and will send the following parameters while redirecting.

| **Parameter** | **Description** |
| :- | :- |
| `order_id` | Order number supplied by you in the payment request. |
| `payment_id` | Unique identifier of the payment which is generated by Pointspay. You use this identifier to specify a Payment, when doing refunds.<br>E.g., 2f47fff25b3e4e7dabe7d8ff8a1a0010 |
| `status` | Status code indicating the status of the request. Few possible status: SUCCESS, FAILED, CANCELED. |
| `authorization` | The authorization code associated with the payment processed. |
| `oauth_signature` | The generated signature, which is unique for each request and ensures the request’s integrity. |

_Table 6_ 

Merchant should verify the form body parameters and auth signature sent while redirection. The steps to do the same are mentioned in the section 5.3 below. 

**Sample link** 

[https://www.example.com/txn_landing_page](https://www.example.com/txn_landing_page) (merchant redirection URL) 

**Sample redirection request body**
```
"order_id": "e97f-45aa-9c6d-1f95",
"payment_id": "eb51e9bb9d2c4166b3b5332273bdff1d",
"status": "SUCCESS",
"authorization": "Bj05vcff67cSHA256withRSA550e8400-e29b-41d4-a716-4466554400001693982469",
"oauth_signature": "dUkcasiWsc00rM5EdctWfvEst+w6tbSgckLDOeC4H3E="
```

### 3.5. Instant Payment Notification (IPN)

After the payment has been processed successfully at Pointspay, the Pointspay server sends an HTTP PUT request with parameters to a pre-configured merchant IPN endpoint. If an IPN endpoint URL is specified in the payment request, the Pointspay server sends the notification to that provided endpoint URL. Refer section 6.1 on how to pass the dynamic IPN URL in the payment request. 

**Merchant endpoint pre-requisites:** 

- Merchant endpoint should be accessible in both HTTP and HTTPS schemes.
- Merchant endpoint character length should not be greater than 1000 characters.

Merchant endpoint should be able to accept a header size up to 8kb. Pointspay will send the following parameters to the merchant endpoint:

| **Parameter** | **Description** |
| :- | :- |
| `order_id` | Order number supplied by you in the payment request. |
| `payment_id` | Unique identifier of the payment which is generated by Pointspay. You use this identifier to specify a payment, when doing refunds.<br>E.g., 2f47fff25b3e4e7dabe7d8ff8a1a0010 |
| `status` | Status code indicating the status of the request.<br>Possible status: SUCCESS. |

_Table 7_

Pointspay also sends an OAuth authorization header with the request. Merchant should verify the request body and signature sent in the request header. The steps to verify the signature are available in section 5.2 below. 


## 4. Refund API 

You can request a partial or full refund. You can request several partial refunds for the same transaction. The sum of all refunds must not be higher than the total amount of the payment transaction. 

The API is secured via OAuth which requires adding OAuth headers and a signature to the request and the response needs to be verified accordingly. Please refer Section 5 below for the details on request-response signatures.

| API URI | /api/v1/refunds |
| :- | :- |
| HTTP Method |POST |

_Table 8_

**Request:** 

| **Parameter** | **Type** | **Mandatory** | **Description** |
| :- | :- | :- | :- |
| `amount` | string | Y | - Refund amount in minor units.<br>- Max 11 characters.<br>- E.g., For a refund amount of USD100.00, pass value as 10000. |
| `payment_id` | string | Y | The Pointspay payment id provided when the payment was initially created. |
| `refund_reason` | string | N | - Reason for refund of the payment.<br>- Max 200 characters. |
| `additional_data` | object | N | Here optional additional information can be passed as part of the request.<br>Please refer section 6. |

_Table 9_

**Response:** 

| **Parameter** | **Type** | **Description** |
| :- | :- | :- |
| `created_at` | string | The Epoch time with milliseconds when the refund transaction was created.<br>e.g., 1694068168722 |
| `payment_id` | string | Unique identifier of the payment transaction in Pointspay. |
| `refund_amount` | string | Amount refunded in the current refund transaction. |
| `refund_id` | string | Unique identifier of the refund transaction in Pointspay. |
| `status` | string | Transaction can be in one of the predefined statuses: SUCCESS, FAILED, REJECTED. |
| `status_message` | string | A more detailed message about the status. |

_Table 10_


## 5. Request/Response signature creation and verification 
1. Add Authorization Header and Signature in the request

The request needs to be signed using a digital certificate. Steps to generate the signature:

1. Sort the request body (parameters in Table 4 for payments and Table 9 for refunds) in alphabetical order. 
1. Minify/compress  the  request  body  so  that  it  doesn’t  contain  any  white  space characters. 
1. Include only non-empty properties in signature. 
4. Append values of OAuth parameters in the body string in the below order to generate the message to be signed.



|**OAuth parameter** (Refer Table 12 for description)|
| - |
|oauth\_consumer\_key|
|oauth\_signature\_method|
|oauth\_nonce|
|oauth\_timestamp|

Table 11 

5. Encrypt  and  sign  the  message  using  the  private  key  as  the  secret  key  using SHA256withRSA algorithm. 
5. Encode the result using Base-64 encoding.
5. The generated output is the OAuth signature.

This digital signature will be used in the “Authorization” header sent with the request. An Authorization header contains the below OAuth parameters:



|**Parameter** ||**Mandatory** |**Description** |
| - | :- | - | - |
|oauth\_consumer\_key||Y |The consumer key provided during merchant onboarding.|
|oauth\_signature\_method||Y |Signature method will always be “SHA256withRSA”.|
|oauth\_nonce||Y |A unique string that changes with each transaction. Typically, a UUID.|
|oauth\_timestamp||Y |A timestamp indicating when the request |
||||was created, typically in milliseconds since the UNIX Epoch.|
|oauth\_signature||Y |The generated signature, which is unique for |
||||each request and ensures the request’s integrity.|

Table 12 

**Note:** These parameters must be added in the Authorization Header in the same order as the above table. Also, please ensure the header size doesn’t exceed 8 KB. 

e.g.  



|**Sample Payment Request Header** |
| - |
|<p>POST /api/v1/payments HTTP/1.1 </p><p>Host:[ https://secure.pointspay.com ](https://secure.pointspay.com/)</p><p>Content-type: application/json </p><p>Authorization: Oauth </p><p>`  `oauth\_consumer\_key=”WqEdR6HN3vTG2csyH2YVp30ySpITobHR”, </p>|

`  `oauth\_signature\_method=”SHA256withRSA”, ![](Aspose.Words.351fea9e-b96b-4879-aff2-f879a5a7dd8e.004.png)

`  `oauth\_nonce=”550e8400-e29b-41d4-a716-446655440000”, 

`  `oauth\_timestamp=”1709912891225”, 

`  `oauth\_signature=”dUkcasiWsc00rM5EdctWfvEst+w6tbSgckLDOeC4H3E=”



|**Sample Payment Body**|
| - |
|{“amount”:”10000”,”currency”:”USD”,”language”:”en”,”order\_id”:” e97f-45aa-9c6d-1f95”, ”shop\_code”:”O7iY1ZMoTwFQ”} |



|**Sample Payment Message to generate signature**|
| - |
|{“amount”:”10000”,”currency”:”USD”,”language”:”en”,”order\_id”:” e97f-45aa-9c6d-1f95”, ”shop\_code”:”O7iY1ZMoTwFQ”}**Bj05vcff67cSHA256withRSA550e8400-e29b-41d4-a716- 4466554400001693982469** |

**Sample code to generate signature body:** 

Code to generate alphabetically ordered JSON body and to append the authorization header parameter to generate signature message:



|String sortAndMinifyBody(String body) throws JsonProcessingException { |
| - |
|ObjectMapper mapper = new ObjectMapper(); |
|TypeReference<TreeMap<String, Object>> typeRef |
|= new TypeReference<TreeMap<String, Object>>() {}; |
||
|// Read as map |
|TreeMap<String,Object> map = mapper.readValue(body, typeRef); |
||
|// Sort properties in alphabetical order |
|mapper.enable(SerializationFeature.ORDER\_MAP\_ENTRIES\_BY\_KEYS); |
|mapper.setSerializationInclusion(JsonInclude.Include.NON\_EMPTY); |
|return mapper.writeValueAsString(map); |
|} |
||
|String appendOauthHeaderParams(String orderedAndMinifiedBody){ |
|String oauthConsumerKey = "your\_consumer\_key"; |
|String oauthSignatureMethod = "your\_oauth\_signature\_method"; |
|String oauthNonce = "unique\_code\_for\_each\_request"; |
|String oauthTimestamp = "epoch\_timestamp\_including\_milliseconds"; |
|StringBuffer sb = new StringBuffer(orderedAndMinifiedBody); |
|sb.append(oauthConsumerKey); |
|sb.append(oauthSignatureMethod); |
|sb.append(oauthNonce); |
|sb.append(oauthTimestamp); |
|return sb.toString(); |
|} |
||
Sample code to generate the OAuth signature:



|String generateSignature(String body, Path storePath, String alias, char[] |
| - |
|keystorePassword, char[] keyPassword) throws Exception{ |
|//Generating an alphabetically sorted and minified json request body |
|string from java object |
|String orderedAndMinifiedBody = sortAndMinifyBody(body); |
|// Appending oauth parameters after the json request body to generate |
|the message to sign. |
|String messageToBeSigned = |
|appendOauthHeaderParams(orderedAndMinifiedBody); |
|// Create a Keystore instance |
|KeyStore keystore = KeyStore.getInstance("PKCS12"); |
|String signatureStr; |
|// Create an Input Stream from the “.p12” keypair |
|try(FileInputStream fis = new FileInputStream (storePath.toFile())) { |
|// Load the keystore and get private key by providing keystore |
|password |
|keystore.load(fis, keystorePassword); |
||
|// Set entry password |
|KeyStore.ProtectionParameter entryPassword = |
|new KeyStore.PasswordProtection(keyPassword); |
|KeyStore.PrivateKeyEntry keyEntry = (KeyStore.PrivateKeyEntry) |
|keystore.getEntry(alias, entryPassword); |
|// Get the private key |
|PrivateKey privateKey = keyEntry.getPrivateKey(); |
|// Create a signature instance of signature object using |
|SHA256withRSA algorithm |
|Signature signature = Signature.getInstance("SHA256withRSA"); |
|// Initialize the signature object for signing using the private key|
|signature.initSign(privateKey); |
|// Update the data to be signed |
||
|signature.update(messageToBeSigned.getBytes(StandardCharsets.UTF\_8)); |
|// Generates the digital signature |
|byte[] signatureBytes = signature.sign(); |
|// Convert the digital signature into text format |
|signatureStr = Base64.getEncoder().encodeToString(signatureBytes); |
|} |
|return signatureStr; |
|} |
||
2. Verify response data and signature 

Pointspay returns the OAuth authorization parameters in the API response header. The merchant should verify the response body and signature returned in the response header. 

**Steps to verify signature:**

1. Sort the response in alphabetical order. 
1. Minify/Compress  the  response  body  so  that  it  doesn’t  contain  any  white  space characters. 
1. Include only non-empty properties for verification.
1. Append values of OAuth parameters in the response body string in the order specified in Table 11 under section 5.1, to generate the response message. 
1. Retrieve the “oauth\_signature” parameter from the response Authorization header.
1. Decode the “oauth\_signature” received from the response Authorization header using the Base64 decoding. 
1. Verify the Base64 decoded response signature with the generated response message bytes using SHA256withRSA algorithm and the public key. 

**Sample code to verify response signature:**

Code to append the authorization header parameter to generate message to be verified:



|String sortAndMinifyBody(String body) throws JsonProcessingException { |
| - |
|ObjectMapper mapper = new ObjectMapper(); |
|TypeReference<TreeMap<String, Object>> typeRef |
|= new TypeReference<TreeMap<String, Object>>() {}; |
||
|// Read as map |
|TreeMap<String,Object> map = mapper.readValue(body, typeRef); |
||
|// Sort properties in alphabetical order |
|mapper.enable(SerializationFeature.ORDER\_MAP\_ENTRIES\_BY\_KEYS); |
|mapper.setSerializationInclusion(JsonInclude.Include.NON\_EMPTY); |
|return mapper.writeValueAsString(map); |
|} |
||
|String appendOauthHeaderParams(String orderedAndMinifiedBody){ |
|String oauthConsumerKey = "your\_consumer\_key"; |
|String oauthSignatureMethod = "your\_oauth\_signature\_method"; |
|String oauthNonce = "unique\_code\_for\_each\_request"; |
|String oauthTimestamp = "epoch\_timestamp\_including\_milliseconds"; |
|StringBuffer sb = new StringBuffer(orderedAndMinifiedBody); |
|sb.append(oauthConsumerKey); |
|sb.append(oauthSignatureMethod); |
|sb.append(oauthNonce); |
|sb.append(oauthTimestamp); |
|return sb.toString(); |
|} |
||
Sample code to verify the OAuth signature:



|boolean verifySignature(String body, String oauthSignature, Path storePath, |
| - |
|String alias, char[] keystorePassword, char[] keyPassword) throws Exception{|
|//Generating am alphabetically sorted and minified json response body |
|string from java object |
|String orderdAndMinifiedBody = sortAndMinifyBody(body); |
|// Appending oauth parameters after the json response body to generate |
|the message to sign. |
|String messageToBeVerified = |
|appendOauthHeaderParams(orderdAndMinifiedBody); |
|//Get the signature header from the request |
|byte[] signatureBytes = Base64.getDecoder().decode(oauthSignature); |
|//Create a keystore instance and load the keystore file from your |
|keystore path |
|KeyStore keystore = KeyStore.getInstance("PKCS12"); |
|try(FileInputStream fis = new FileInputStream (storePath.toFile())) { |
|keystore.load(fis, keystorePassword); |
|// Set entry password |
|KeyStore.ProtectionParameter entryPassword = |
|new KeyStore.PasswordProtection(keyPassword); |
|KeyStore.PrivateKeyEntry keyEntry = (KeyStore.PrivateKeyEntry) |
|keystore.getEntry(alias, entryPassword); |
|// Get public key from keystore |
|Certificate certificate = keyEntry.getCertificate(); |
|PublicKey publicKey = null; |
|if (certificate != null) { |
|publicKey = certificate.getPublicKey(); |
|} |
|if (publicKey != null) { |
|// Create a message byte array from the messageToBeVerified |
|string |
|byte[] messageBytes = |
|messageToBeVerified.getBytes(StandardCharsets.UTF\_8); |
|// Instantiate the signature object with "SHA256withRSA" |
|algorithm |
|Signature signature = Signature.getInstance("SHA256withRSA"); |
|signature.initVerify(publicKey); // Provide public key to the |
|signature object |
|signature.update(messageBytes); // Update the message bytes in |
|the signature object |
|return signature.verify(signatureBytes); // Verify the signature|
|} else { |
|return false; |
|} |
|} |
|} |

3. Verify request param and signature in merchant redirection.

   The merchant should verify the request body parameters with the signature.



|**Sample redirection request body**|
| - |
|"order\_id ": "e97f-45aa-9c6d-1f95", |
|"payment\_id ": "eb51e9bb9d2c4166b3b5332273bdff1d", |
|"status ": "SUCCESS", |
|"authorization": "Bj05vcff67cSHA256withRSA550e8400-e29b-41d4-a716 -|
|4466554400001693982469", |
|“oauth\_signature”:"dUkcasiWsc00rM5EdctWfvEst+w6tbSgckLDOeC4H3E="|

`   `**Verify the order\_id**

Verify the order\_id in the redirection response body parameter against your order id. **Steps to verify request param and signature:** 

1. Append the parameters order\_id,  payment\_id, status, and authorization from the  request body shown in Table 6 above. 
1. Retrieve the “oauth\_signature” parameter from the request body. 
1. Verify the request signature with the generated final message using SHA256withRSA algorithm and the public key. 

Refer below Java code sample below to verify the request param and signature. Append values from the request body param to create the message to be verified.



|String createMessageToBeVerified(){ |
| - |
|String orderId = "Read order\_id parameter from the redirect request |
|param "; |
|String paymentId = "Read payment\_id parameter from the redirect |
|request param"; |
|String status = "Read status parameter from the redirect request |
|param "; |
|String authorization = "read authorization parameter from the |
|redirect request param "; |
|return orderId + paymentId + status + authorization; |
|} |

Sample code to verify the message with signature:



|boolean verifySignature(String messageToBeVerified, String oauthSignature, |
| - |
|Path storePath, String alias, char[] keystorePassword, char[] keyPassword) |
|throws Exception { |
|//Get the signature header from the request |
|byte[] signatureBytes = Base64.getDecoder().decode(oauthSignature); |
||
|//Create a keystore instance and load the keystore file from your |
|keystore path |
|KeyStore keystore = KeyStore.getInstance("PKCS12"); |
|try(FileInputStream fis = new FileInputStream (storePath.toFile())) { |
|keystore.load(fis, keystorePassword); |
|// Set entry password |
|KeyStore.ProtectionParameter entryPassword = |
|new KeyStore.PasswordProtection(keyPassword); |
|KeyStore.PrivateKeyEntry keyEntry = (KeyStore.PrivateKeyEntry) |
|keystore.getEntry(alias, entryPassword); |
|// Get public key from keystore |
|Certificate certificate = keyEntry.getCertificate(); |
|PublicKey publicKey = null; |
|if (certificate != null) { |
|publicKey = certificate.getPublicKey(); |
|} |
|if (publicKey != null) { |
|// Create a message byte array from the messageToBeVerified |
|string |
|byte[] messageBytes = |
|messageToBeVerified.getBytes(StandardCharsets.UTF\_8); |
|// Instantiate the signature object with "SHA256withRSA" |
|algorithm |
|Signature signature = Signature.getInstance("SHA256withRSA"); |
|signature.initVerify(publicKey); // Provide public key to the |
|signature object |
|signature.update(messageBytes); // Update the message bytes in |
|the signature object |
|return signature.verify(signatureBytes); // Verify the signature|
|} else { |
|return false; |
|} |
|} |
|} |
||
6. Additional Data 

This section contains details of additional information, Merchant may or may not send during payment.



|**Parameter** |**Type** |**Mandatory** |**Description** |
| - | - | - | - |
|dynamic\_urls |object |N |Refer Section 6.1 |
|categories|List<object> |N |Refer Section 6.2 |

Table 13 

1. Dynamic URLs 

You can set up default static URLs for your shop during onboarding or can include them dynamically with each transaction you create. The default static URLs would apply If you don't include them dynamically in each payment request. 

If you haven't set the default success, failure and cancel redirect URLs during on-boarding and  you  are  also  not  sending  corresponding  dynamic  redirection  URLs  during  the payment  request,  you  will  get  an  error  (REDIRECT\_URL\_MISSING)  while  creating  a transaction. Please refer the section 7.2 for more details.



|**Parameter** |**Type** |**Mandatory** |**Description** |
| - | - | - | - |
|success|string |N |<p>- The URL to which the shopper would be redirected when the payment is successful.</p><p>- 200 characters maximum.</p>|
|failure |string |N |<p>- The URL to which the shopper would be redirected when the payment fails. </p><p>- 200 characters maximum.</p>|
|cancel |string |N |<p>- The URL to which the shopper would be redirected when the payment is cancelled by the user.  </p><p>- 200 characters maximum.</p>|
|ipn |string |N |<p>￿  A merchant endpoint URL to which a </p><p>notification will be sent after a successful payment.</p><p>￿ ￿ </p><p>200 characters maximum.</p><p>Refer Section 3.5</p>|

Table 14 

2. Categories

It is the list of product categories with amount per category.



|**Parameter** |**Type** |**Mandatory** |**Description** |
| - | - | - | - |
|amount |string |N |<p>￿  The category-specific amount in minor </p><p>units. </p><p>￿ ￿ </p><p>Max 11 characters. </p><p>E.g., For a category amount of USD 100.00, pass value as 10000.</p>|
|code |string |N |<p>￿  It is the category code. It should be unique</p><p>for each category. </p>|

Table 15 

7. Metadata
1. Possible POST/GET response codes



|**Code** |**Description** |
| - | - |
|200 OK** |The request was successful, and the response body contains the representation requested.|
|302 FOUND |A common redirect response; you can GET the representation at the URI in the Location response header.|
|304 NOT MODIFIED |Your client's cached version of the representation is still up to date. |
|400 BAD REQUEST |The request you are sending is not a valid one. It is not aligned with the specs.|
|401 UNAUTHORIZED |The supplied credentials, if any, are not sufficient to access the resource. |
|404 NOT FOUND** |The requested endpoint URI is invalid.|
|429 TOO MANY REQUESTS |Your application is sending too many simultaneous requests.|
|500  SERVER ERROR |We couldn't return the representation due to an internal server error. |
|503 SERVICE UNAVAILABLE |We are temporarily unable to return the representation. Please wait and try again later.|

Table 16 

2. Possible error codes



|**Error code** |**Error message**|**HTTP  status code** |
| - | - | :- |
|SERVER\_ERROR |Server error. |500 |
|UNABLE\_TO\_PROCESS\_THE\_REQUEST |Unable to process the request. Usually happens when external payment networks are unavailable. You can try later.|500 |
|UNKNOWN\_ERROR |An unknown error happened on the server. Please contact Pointspay support if you’re encountering this error persistently. |500 |
|TRANSACTION\_NOT\_FOUND |Payment with the provided ID was not found. Please check if Payment ID is valid.|404 |
|INVALID\_PARAMETERS |You will get this code when you are sending an invalid request, if one or more parameters in the request are not valid.|400 |
|SHOP\_NOT\_FOUND |Merchant cannot be found. Please check your shop code. |400 |
|SHOP\_STATUS\_INVALID |Pointspay payments are not available for the shop code. Please check the status of your account.|400 |
|REDIRECT\_URL\_MISSING |Any one of success, failure or cancel redirection URL is missing for the shop.|500 |
|INVALID\_SHOP\_CODE |Shop code is invalid.|400 |
|INELIGIBLE\_TRANSACTION\_STATUS |You are trying to perform an operation which is not available for the current status of the transaction. For example, a transaction can be refunded only when |500 |
||the payment status is |||
| :- | - | :- | :- |
||*SUCCESS*. |||
|CURRENCY\_NOT\_SUPPORTED |You are using an ||400 |
||unsupported currency.|||
|REFUND\_AMOUNT\_EXCEEDED |Refund amount exceeded. ||500 |
||You cannot refund more |||
||than what was initially |||
||paid. |||
|INVALID\_CATEGORY |Invalid category||500 |
|REFUND\_CATEGORY\_AMOUNT\_EXCEED\_|Refund category amount ||500 |
|AVAILABLE\_CATEGORY\_AMOUNT |exceeds available |||
||category amount|||
|DUPLICATE\_CATEGORY |Duplicate category||400 |
|CATEGORY\_AMOUNT\_EXCEED\_TXN\_AM|Category amount exceed|s |400 |
|OUNT |transaction amount|||
|||||
|REFUND\_CATEGORY\_AMOUNT\_EXCEED\_|Refund category amount ||400 |
|REFUND\_TXN\_AMOUNT |exceeds refund transaction |||
||amount |||
|INVALID\_OAUTH\_TIMESTAMP |The provided OAuth ||401 |
||timestamp is invalid or has |||
||expired. |||
|MISSING\_AUTHORIZATION\_HEADER |OAuth Authorization ||401 |
||header is missing in the |||
||request. |||
|MISSING\_AUTHORIZATION\_HEADER\_PARA|{{Parameter-Names}} ||401 |
|METERS |Authorization header |||
||parameters are missing in |||
||the request.|||
|MISSING\_AUTHORIZATION\_HEADER\_PARA|{{Parameter-Name}} ||401 |
|METER |Authorization header |||
||parameter Is missing in the |||
||request. |||
|INVALID\_AUTHORIZATION\_HEADER |An invalid OAuth ||401 |
||Authorization header |||
||format has been passed in |||
||the request.|||
|INVALID\_OAUTH\_CONSUMER\_KEY |The value for ||401 |
||oauth\_consumer\_key |||
||doesn't match an existing |||
||key or doesn't have access to the requested API.|||
|INVALID\_OAUTH\_SIGNATURE\_METHOD |The value for oauth\_signature\_method is invalid or is not supported.|401 ||
|INVALID\_OAUTH\_NONCE |The value for oauth\_nonce was already used. Make sure you send a unique nonce with each request.|401 ||
|SIGNATURE\_VERIFICATION\_FAILED |OAuth signature verification failed.|401 ||

Table 17 

3. Sample error format



|**Sample Error Body**|
| - |
|{"code": " INVALID\_PAYMENT\_ID ","message": " Payment ID does not exist.", "key": " INVALID\_PAYMENT\_ID "}|

Table 18 
www.pointspay.com Page 23 of 23

[ref1]: Aspose.Words.351fea9e-b96b-4879-aff2-f879a5a7dd8e.001.png
