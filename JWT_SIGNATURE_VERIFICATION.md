 # JWT Signature Verification Guide for Pointspay

This guide shows how to verify an RS256 JWT issued by Pointspay style services using the JWKS published at: `https://{domain}/.well-known/jwks.json`

So the JWKS endpoints are respectively:

- UAT: `https://uat-api.pointspay.com/.well-known/jwks.json`

- Prod: `https://api.pointspay.com/.well-known/jwks.json`

You: (a) discover the matching JWK by `kid`, (b) construct/parse the RSA public key, (c) verify the signature and required claims.

> Security note: Never trust the header `alg` blindly; enforce the expected algorithm (RS256). Always validate audience, issuer, expiration and (optionally) nonce / subject according to your business rules.


# Step-by-Step Instructions

1. Get the JWT from Pointspay, for example:


```
eyJhbGciOiJSUzI1NiIsImtpZCI6InBwLWRlbW8ta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJjdXIiOiJBRUQiLCJzdGF0IjoiQ0FQVFVSRUQiLCJwYWNjIjo4NSwidnBhIjoxLjUsImlzcyI6InBvaW50c3BheSIsImFtdCI6MTEyNTAsInBpZCI6IjI3MWQyZjMyZmNiZjQzMDA4MGNhYjE2ZDY4MTBjOGNjIiwib2lkIjoiMzkiLCJub25jZSI6IjJmYmNhMzZjLTBjOWEtNDc3MC05N2QwLWUzZTBkNGJlNzlhOSIsImF1ZCI6InlvdXItYXVkaWVuY2UtaGVyZSIsInByZWQiOjAsInZwciI6MC43MywiaWF0IjoxNzU5NDg5MTM0LCJleHAiOjE3NTk0ODk3MzR9.HE3I660wzQVgUtzsc7LKFIBdEx9w-G1TrLRTB3Y8PyvV-q1S7kwau252TowZYTuraUqDfEpqMsDcEJusUMJ_RIE0-2rLk1Su_shpzBT271nX9EZoAQLPbgE75gKe0e4Sb0z37Jb2uQXvWRRhiTiOlFAxG06TC2vs0usO9Kpuu_fZhBgSVbx_CXE8HC3Zj0cKkkm8z8Y-MhqdFwZVOxxo40joojMlZBCMB6RaIEZ6ebk-fMOBDy0iSc8UV7iDWJJJBnMaEbaSVpI83-i6C0ltY93pYxotcoQL0UaWFNYf0fR1WxNHNJzIDFpjPZ0XU9iArN8fEFoJ_ruOYdqNOJfLRQ
```

2. Fetch the JWKS from the appropriate endpoint (UAT or Prod).

Example: https://uat-api.pointspay.com/.well-known/jwks.json

```json 
{
  "keys": [
	{
	  "kty": "RSA",
	  "kid": "pp-demo-key-1",
	  "alg": "RS256",
	  "use": "sig",
	  "n": "0QixhydcdBGt2Ja3dtEkBCsYorsyi_wrudLZpaT4rdtk08qFv1l9Aq8AUFLirX7yEJKg9hGyWDjEhRu3erjfUotMCMVYq9rkFZ1tw_h4mcllYck3EpAKaazWyOiyTEXpnHQf7xXTNEpwGLOVOHF61MJEAOBK_B3gqGiMihRwZQDsnFuVqOHi18h89zxnniHucsuO4JawWhUkuXm2ToOad4Rza1zJ1UI0sPJHgLwEMPtiZzJXT0HYdhhAHfvkjprEO6F4W7bEeSsbMrLBpGrFobKvW-TV7iUs9YNyI1cp0fi9KqXd5OeecCUly-hAaMtpQ2CSUqfbLppEA628KsYg_Q",
	  "e": "AQAB",
	  "x-pp-scheme": "pp-v1"
	}
  ]
}
```

Best would be to cache the JWKS respecting `Cache-Control` headers.

3. Validate the JWT using one of the examples below or your own code.

In production you may see multiple keys; pick the one whose `kid` matches the JWT header.

---
## Example Signed JWT

Header.payload.signature (line breaks added here for readability only):

```
eyJhbGciOiJSUzI1NiIsImtpZCI6InBwLWRlbW8ta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJjdXIiOiJBRUQiLCJzdGF0IjoiQ0FQVFVSRUQiLCJwYWNjIjo4NSwidnBhIjoxLjUsImlzcyI6InBvaW50c3BheSIsImFtdCI6MTEyNTAsInBpZCI6IjI3MWQyZjMyZmNiZjQzMDA4MGNhYjE2ZDY4MTBjOGNjIiwib2lkIjoiMzkiLCJub25jZSI6IjJmYmNhMzZjLTBjOWEtNDc3MC05N2QwLWUzZTBkNGJlNzlhOSIsImF1ZCI6InlvdXItYXVkaWVuY2UtaGVyZSIsInByZWQiOjAsInZwciI6MC43MywiaWF0IjoxNzU5NDg5MTM0LCJleHAiOjE3NTk0ODk3MzR9.HE3I660wzQVgUtzsc7LKFIBdEx9w-G1TrLRTB3Y8PyvV-q1S7kwau252TowZYTuraUqDfEpqMsDcEJusUMJ_RIE0-2rLk1Su_shpzBT271nX9EZoAQLPbgE75gKe0e4Sb0z37Jb2uQXvWRRhiTiOlFAxG06TC2vs0usO9Kpuu_fZhBgSVbx_CXE8HC3Zj0cKkkm8z8Y-MhqdFwZVOxxo40joojMlZBCMB6RaIEZ6ebk-fMOBDy0iSc8UV7iDWJJJBnMaEbaSVpI83-i6C0ltY93pYxotcoQL0UaWFNYf0fR1WxNHNJzIDFpjPZ0XU9iArN8fEFoJ_ruOYdqNOJfLRQ
```

Decoded payload (claims):

```json
{
  "cur": "AED",
  "stat": "CAPTURED",
  "pacc": 85,
  "vpa": 1.5,
  "iss": "pointspay",
  "amt": 11250,
  "pid": "271d2f32fcbf430080cab16d6810c8cc",
  "oid": "39",
  "nonce": "2fbca36c-0c9a-4770-97d0-e3e0d4be79a9",
  "aud": "your-audience-here",
  "pred": 0,
  "vpr": 0.73,
  "iat": 1759488721,
  "exp": 1759489321
}
```

---
### Validation Checklist

Required steps your code should perform:
1. Split token into header, payload, signature (a library will do this)
2. Base64url decode header; extract `kid`, verify `alg == RS256`
3. Fetch JWKS once (cache with respect to `Cache-Control` / TTL)
4. Find JWK with same `kid`; construct RSA public key from `n` and `e`
5. Verify signature with RSASSA-PKCS1-v1_5 SHA-256 (RS256)
6. Validate claims:
   - `iss` equals expected issuer (e.g. `pointspay`)
   - `aud` matches one of your allowed audiences (your domain)
   - `exp` in the future; `iat` not too far in past/future (clock skew)
   - Optional: `nonce`, business fields (`stat`, `amt`, etc.)
7. Reject if any step fails.

---
### Language Examples

For brevity examples fetch the JWKS just-in-time; production code should cache it.

### 4.1 JavaScript (Node.js, using jose)
Install: `npm install jose`

```js
import { createRemoteJWKSet, jwtVerify } from 'jose';

const JWKS_URL = 'https://{yourDomain}/.well-known/jwks.json';
const EXPECTED_ISS = 'pointspay';
const EXPECTED_AUD = 'your-audience-here';

// Create a cached remote JWK set fetcher
const jwks = createRemoteJWKSet(new URL(JWKS_URL));

async function verifyToken(token) {
  const { payload, protectedHeader } = await jwtVerify(token, jwks, {
	issuer: EXPECTED_ISS,
	audience: EXPECTED_AUD,
	algorithms: ['RS256'],
  });
  // Additional business validations
  if (payload.stat !== 'CAPTURED') throw new Error('Unexpected status');
  return payload;
}

// Demo usage (replace with the live token you receive):
const demoToken = 'eyJhbGciOiJSUzI1NiIsImtpZCI6InBwLWRlbW8ta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJjdXIiOiJBRUQiLCJzdGF0IjoiQ0FQVFVSRUQiLCJwYWNjIjo4NSwidnBhIjoxLjUsImlzcyI6InBvaW50c3BheSIsImFtdCI6MTEyNTAsInBpZCI6IjI3MWQyZjMyZmNiZjQzMDA4MGNhYjE2ZDY4MTBjOGNjIiwib2lkIjoiMzkiLCJub25jZSI6IjJmYmNhMzZjLTBjOWEtNDc3MC05N2QwLWUzZTBkNGJlNzlhOSIsImF1ZCI6InlvdXItYXVkaWVuY2UtaGVyZSIsInByZWQiOjAsInZwciI6MC43MywiaWF0IjoxNzU5NDg5MTM0LCJleHAiOjE3NTk0ODk3MzR9.HE3I660wzQVgUtzsc7LKFIBdEx9w-G1TrLRTB3Y8PyvV-q1S7kwau252TowZYTuraUqDfEpqMsDcEJusUMJ_RIE0-2rLk1Su_shpzBT271nX9EZoAQLPbgE75gKe0e4Sb0z37Jb2uQXvWRRhiTiOlFAxG06TC2vs0usO9Kpuu_fZhBgSVbx_CXE8HC3Zj0cKkkm8z8Y-MhqdFwZVOxxo40joojMlZBCMB6RaIEZ6ebk-fMOBDy0iSc8UV7iDWJJJBnMaEbaSVpI83-i6C0ltY93pYxotcoQL0UaWFNYf0fR1WxNHNJzIDFpjPZ0XU9iArN8fEFoJ_ruOYdqNOJfLRQ';
verifyToken(demoToken).then(p => console.log('Valid payload', p)).catch(e => console.error('Invalid', e));
```

### 4.2 PHP (firebase/php-jwt – concise)
Install: `composer require firebase/php-jwt`

```php
<?php
require 'vendor/autoload.php';

use Firebase\JWT\JWT; // v6+
use Firebase\JWT\Key;
use phpseclib3\Math\BigInteger;
use phpseclib3\Crypt\RSA;

$JWKS_URL = 'https://{pointspay_domain}/.well-known/jwks.json';
$EXPECTED_ISS = 'pointspay';
$EXPECTED_AUD = 'your-audience-here';

$token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6InBwLWRlbW8ta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJjdXIiOiJBRUQiLCJzdGF0IjoiQ0FQVFVSRUQiLCJwYWNjIjo4NSwidnBhIjoxLjUsImlzcyI6InBvaW50c3BheSIsImFtdCI6MTEyNTAsInBpZCI6IjI3MWQyZjMyZmNiZjQzMDA4MGNhYjE2ZDY4MTBjOGNjIiwib2lkIjoiMzkiLCJub25jZSI6IjJmYmNhMzZjLTBjOWEtNDc3MC05N2QwLWUzZTBkNGJlNzlhOSIsImF1ZCI6InlvdXItYXVkaWVuY2UtaGVyZSIsInByZWQiOjAsInZwciI6MC43MywiaWF0IjoxNzU5NDg5MTM0LCJleHAiOjE3NTk0ODk3MzR9.HE3I660wzQVgUtzsc7LKFIBdEx9w-G1TrLRTB3Y8PyvV-q1S7kwau252TowZYTuraUqDfEpqMsDcEJusUMJ_RIE0-2rLk1Su_shpzBT271nX9EZoAQLPbgE75gKe0e4Sb0z37Jb2uQXvWRRhiTiOlFAxG06TC2vs0usO9Kpuu_fZhBgSVbx_CXE8HC3Zj0cKkkm8z8Y-MhqdFwZVOxxo40joojMlZBCMB6RaIEZ6ebk-fMOBDy0iSc8UV7iDWJJJBnMaEbaSVpI83-i6C0ltY93pYxotcoQL0UaWFNYf0fR1WxNHNJzIDFpjPZ0XU9iArN8fEFoJ_ruOYdqNOJfLRQ';

function base64url_decode_str(string $v): string {
    $pad = strlen($v) % 4;
    if ($pad) $v .= str_repeat('=', 4 - $pad);
    return base64_decode(strtr($v, '-_', '+/'));
}

function jwk_to_pem(array $jwk): string {
    if (($jwk['kty'] ?? '') !== 'RSA') {
        throw new InvalidArgumentException('Only RSA keys supported');
    }
    $n = new BigInteger(base64url_decode_str($jwk['n']), 256);
    $e = new BigInteger(base64url_decode_str($jwk['e']), 256);

    $rsa = RSA::loadPublicKey([
        'n' => $n,
        'e' => $e,
    ]);
    // PKCS8 (SubjectPublicKeyInfo). Use 'PKCS1' if you prefer the raw RSA form.
    return $rsa->toString('PKCS8');
}

// --- Parse header (no signature verification yet) ---
$parts = explode('.', $token);
if (count($parts)!==3) throw new RuntimeException('Malformed token');
$header = JWT::jsonDecode(JWT::urlsafeB64Decode($parts[0]));
if (($header->alg ?? null) !== 'RS256') throw new RuntimeException('Unexpected alg');
$kid = $header->kid ?? null; if (!$kid) throw new RuntimeException('Missing kid');

// --- Fetch JWKS & locate key ---
$jwks = json_decode(file_get_contents($JWKS_URL), true, flags: JSON_THROW_ON_ERROR);
$jwk = null; foreach ($jwks['keys'] as $k) { if (($k['kid'] ?? null)===$kid) { $jwk=$k; break; } }
if (!$jwk) throw new RuntimeException('kid not found in JWKS');

// --- Build PEM & verify ---
$publicKey = jwk_to_pem($jwk);
$claims = JWT::decode($token, new Key($publicKey, 'RS256'));

// --- Claim validation ---
if (($claims->iss ?? null) !== $EXPECTED_ISS) throw new RuntimeException('Bad iss');
$aud = $claims->aud ?? null; $audList = is_array($aud) ? $aud : [$aud];
if (!in_array($EXPECTED_AUD, $audList, true)) throw new RuntimeException('Bad aud');
if (($claims->stat ?? null) !== 'CAPTURED') throw new RuntimeException('Unexpected stat');

var_dump($claims); // Valid
```

### 4.3 Python (pyjwt + cryptography)
Install: `pip install pyjwt cryptography requests`

```python
import base64, json, requests, time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt

JWKS_URL = 'https://{yourDomain}/.well-known/jwks.json'
EXPECTED_ISS = 'pointspay'
EXPECTED_AUD = 'your-audience-here'

def b64url_to_int(val: str) -> int:
	padding = '=' * (-len(val) % 4)
	return int.from_bytes(base64.urlsafe_b64decode(val + padding), 'big')

def jwk_to_public_key(jwk):
	n_int = b64url_to_int(jwk['n'])
	e_int = b64url_to_int(jwk['e'])
	public_numbers = rsa.RSAPublicNumbers(e_int, n_int)
	return public_numbers.public_key()

def fetch_jwks():
	return requests.get(JWKS_URL, timeout=5).json()

def find_jwk(jwks, kid):
	for k in jwks['keys']:
		if k['kid'] == kid:
			return k
	raise ValueError('kid not found')

def verify(token: str):
	headers = jwt.get_unverified_header(token)
	if headers.get('alg') != 'RS256':
		raise ValueError('Unexpected alg')
	jwk = find_jwk(fetch_jwks(), headers['kid'])
	pub_key = jwk_to_public_key(jwk)
	payload = jwt.decode(
		token,
		pub_key,
		algorithms=['RS256'],
		audience=EXPECTED_AUD,
		issuer=EXPECTED_ISS,
		options={'require': ['exp', 'iat', 'iss', 'aud']}
	)
	if payload.get('stat') != 'CAPTURED':
		raise ValueError('Unexpected stat')
	return payload

demo_token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6InBwLWRlbW8ta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJjdXIiOiJBRUQiLCJzdGF0IjoiQ0FQVFVSRUQiLCJwYWNjIjo4NSwidnBhIjoxLjUsImlzcyI6InBvaW50c3BheSIsImFtdCI6MTEyNTAsInBpZCI6IjI3MWQyZjMyZmNiZjQzMDA4MGNhYjE2ZDY4MTBjOGNjIiwib2lkIjoiMzkiLCJub25jZSI6IjJmYmNhMzZjLTBjOWEtNDc3MC05N2QwLWUzZTBkNGJlNzlhOSIsImF1ZCI6InlvdXItYXVkaWVuY2UtaGVyZSIsInByZWQiOjAsInZwciI6MC43MywiaWF0IjoxNzU5NDg5MTM0LCJleHAiOjE3NTk0ODk3MzR9.HE3I660wzQVgUtzsc7LKFIBdEx9w-G1TrLRTB3Y8PyvV-q1S7kwau252TowZYTuraUqDfEpqMsDcEJusUMJ_RIE0-2rLk1Su_shpzBT271nX9EZoAQLPbgE75gKe0e4Sb0z37Jb2uQXvWRRhiTiOlFAxG06TC2vs0usO9Kpuu_fZhBgSVbx_CXE8HC3Zj0cKkkm8z8Y-MhqdFwZVOxxo40joojMlZBCMB6RaIEZ6ebk-fMOBDy0iSc8UV7iDWJJJBnMaEbaSVpI83-i6C0ltY93pYxotcoQL0UaWFNYf0fR1WxNHNJzIDFpjPZ0XU9iArN8fEFoJ_ruOYdqNOJfLRQ'
print(verify(demo_token))
```

### 4.4 Java (Nimbus JOSE + JWT)
Maven dependency:

```xml
<dependency>
  <groupId>com.nimbusds</groupId>
  <artifactId>nimbus-jose-jwt</artifactId>
  <version>9.37.3</version>
</dependency>
```

Code snippet:

```java
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.jwk.JWK;
import com.nimbusds.jose.jwk.JWKMatcher;
import com.nimbusds.jose.jwk.JWKSelector;
import com.nimbusds.jose.jwk.source.RemoteJWKSet;
import com.nimbusds.jose.proc.*;
import com.nimbusds.jwt.SignedJWT;
import com.nimbusds.jwt.proc.*;

import java.net.URL;
import java.text.ParseException;

public class JwtVerifier {
	private static final String JWKS_URL = "https://{yourDomain}/.well-known/jwks.json";
	private static final String EXPECTED_ISS = "pointspay";
	private static final String EXPECTED_AUD = "your-audience-here";

	public static void main(String[] args) throws Exception {
		String token = "eyJhbGciOiJSUzI1NiIsImtpZCI6InBwLWRlbW8ta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJjdXIiOiJBRUQiLCJzdGF0IjoiQ0FQVFVSRUQiLCJwYWNjIjo4NSwidnBhIjoxLjUsImlzcyI6InBvaW50c3BheSIsImFtdCI6MTEyNTAsInBpZCI6IjI3MWQyZjMyZmNiZjQzMDA4MGNhYjE2ZDY4MTBjOGNjIiwib2lkIjoiMzkiLCJub25jZSI6IjJmYmNhMzZjLTBjOWEtNDc3MC05N2QwLWUzZTBkNGJlNzlhOSIsImF1ZCI6InlvdXItYXVkaWVuY2UtaGVyZSIsInByZWQiOjAsInZwciI6MC43MywiaWF0IjoxNzU5NDg5MTM0LCJleHAiOjE3NTk0ODk3MzR9.HE3I660wzQVgUtzsc7LKFIBdEx9w-G1TrLRTB3Y8PyvV-q1S7kwau252TowZYTuraUqDfEpqMsDcEJusUMJ_RIE0-2rLk1Su_shpzBT271nX9EZoAQLPbgE75gKe0e4Sb0z37Jb2uQXvWRRhiTiOlFAxG06TC2vs0usO9Kpuu_fZhBgSVbx_CXE8HC3Zj0cKkkm8z8Y-MhqdFwZVOxxo40joojMlZBCMB6RaIEZ6ebk-fMOBDy0iSc8UV7iDWJJJBnMaEbaSVpI83-i6C0ltY93pYxotcoQL0UaWFNYf0fR1WxNHNJzIDFpjPZ0XU9iArN8fEFoJ_ruOYdqNOJfLRQ";

		SignedJWT jwt = SignedJWT.parse(token);
		if (!JWSAlgorithm.RS256.equals(jwt.getHeader().getAlgorithm())) {
			throw new IllegalStateException("Unexpected alg");
		}

		RemoteJWKSet<?> jwkSet = new RemoteJWKSet<>(new URL(JWKS_URL));
		ConfigurableJWTProcessor<?> processor = new DefaultJWTProcessor<>();
		JWSKeySelector<?> keySelector = new JWSVerificationKeySelector<>(JWSAlgorithm.RS256, jwkSet);
		processor.setJWSKeySelector(keySelector);

		JWTClaimsSetVerifier<?> claimsVerifier = (claims, context) -> {
			if (!EXPECTED_ISS.equals(claims.getIssuer())) throw new BadJWTException("Bad iss");
			if (claims.getAudience() == null || !claims.getAudience().contains(EXPECTED_AUD)) throw new BadJWTException("Bad aud");
			if (!"CAPTURED".equals(claims.getStringClaim("stat"))) throw new BadJWTException("Unexpected stat");
		};
		processor.setJWTClaimsSetVerifier(claimsVerifier);

		processor.process(jwt, null); // If no exception, token is valid
		System.out.println("Token valid. amt=" + jwt.getJWTClaimsSet().getLongClaim("amt"));
	}
}
```

---
## 5. Common Pitfalls
| Issue | Explanation | Fix |
|-------|-------------|-----|
| Using wrong algorithm | Token header says RS256 but code allows HS256 | Explicitly whitelist RS256 |
| Kid rotation | New key appears, old one removed | Cache JWKS with short TTL; refetch on kid miss |
| Clock skew | Minor diff in server times fails exp/iat | Allow small leeway (e.g. 60s) |
| Not checking audience | Any site could reuse token | Enforce exact expected audience |
| Accepting expired token | Missing exp check | Use library options to require exp |