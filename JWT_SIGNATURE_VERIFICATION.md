 # JWT Signature Verification Guide for Pointspay

This guide shows how to verify JWT tokens issued by Pointspay services following **[JWT.IO](https://jwt.io)** standards (RFC 7519) with RSA signature verification. PointsPay uses OpenID Connect (OIDC) discovery and JSON Web Key Set (JWKS) for secure token verification.

## JWKS Endpoints

- UAT: `https://uat-api.pointspay.com/.well-known/jwks.json`
- Prod: `https://api.pointspay.com/.well-known/jwks.json`

## JWT.IO Standard Compliance

Our implementation follows JWT.IO standards by:
1. **Algorithm Enforcement**: Explicitly whitelist RS256/RS384/RS512 (never trust header `alg` blindly)
2. **Signature Verification**: Use RSA public keys from JWKS with proper key rotation support
3. **Standard Claims Validation**: Verify `iss` (issuer URL), `aud` (audience), `exp` (expiration), `iat` (issued at)
4. **Key Discovery**: Leverage OIDC discovery (`/.well-known/openid-configuration`) for automatic JWKS URI resolution
5. **Dynamic Audience**: Support per-client audience identifiers (multi-tenant security)

> **Security Note**: Never trust the header `alg` blindly; enforce the expected algorithm (RS256/RS384/RS512). Always validate audience, issuer URL, expiration and (optionally) nonce / subject according to your business rules.

# Verification Process

PointsPay token verification follows the JWT.IO standard workflow:

1. **Parse Token Structure**: Split JWT into header.payload.signature components
2. **Extract Metadata**: Decode header to get `kid` (Key ID) and `alg` (algorithm)
3. **Algorithm Enforcement**: Verify `alg` is RS256, RS384, or RS512 (reject unexpected algorithms)
4. **Public Key Discovery**: 
   - Use OIDC discovery endpoint: `{issuer}/.well-known/openid-configuration`
   - Fetch JWKS from the `jwks_uri` endpoint
   - Locate public key matching the token's `kid`
5. **Signature Verification**: Verify RSA signature using RSASSA-PKCS1-v1_5 with SHA-256/SHA-384/SHA-512
6. **Claims Validation**:
   - `iss` (issuer): Matches expected PointsPay issuer URL (e.g., `https://api.pointspay.com/v4`)
   - `aud` (audience): Matches your unique client/merchant ID
   - `exp` (expiration): Token not expired (with clock skew tolerance)
   - `iat` (issued at): Token issued at reasonable time
   - Business claims: `stat`, `amt`, `oid`, etc.
7. **Return Decoded Payload**: If all validations pass

## Token Example


```
eyJhbGciOiJSUzI1NiIsImtpZCI6InBwLWRlbW8ta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJjdXIiOiJBRUQiLCJzdGF0IjoiQ0FQVFVSRUQiLCJwYWNjIjo4NSwidnBhIjoxLjUsImlzcyI6InBvaW50c3BheSIsImFtdCI6MTEyNTAsInBpZCI6IjI3MWQyZjMyZmNiZjQzMDA4MGNhYjE2ZDY4MTBjOGNjIiwib2lkIjoiMzkiLCJub25jZSI6IjJmYmNhMzZjLTBjOWEtNDc3MC05N2QwLWUzZTBkNGJlNzlhOSIsImF1ZCI6InlvdXItYXVkaWVuY2UtaGVyZSIsInByZWQiOjAsInZwciI6MC43MywiaWF0IjoxNzU5NDg5MTM0LCJleHAiOjE3NTk0ODk3MzR9.HE3I660wzQVgUtzsc7LKFIBdEx9w-G1TrLRTB3Y8PyvV-q1S7kwau252TowZYTuraUqDfEpqMsDcEJusUMJ_RIE0-2rLk1Su_shpzBT271nX9EZoAQLPbgE75gKe0e4Sb0z37Jb2uQXvWRRhiTiOlFAxG06TC2vs0usO9Kpuu_fZhBgSVbx_CXE8HC3Zj0cKkkm8z8Y-MhqdFwZVOxxo40joojMlZBCMB6RaIEZ6ebk-fMOBDy0iSc8UV7iDWJJJBnMaEbaSVpI83-i6C0ltY93pYxotcoQL0UaWFNYf0fR1WxNHNJzIDFpjPZ0XU9iArN8fEFoJ_ruOYdqNOJfLRQ
```

## JWKS Discovery

Fetch the JWKS from the appropriate endpoint (UAT or Prod).

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

**Best Practice**: Cache the JWKS respecting `Cache-Control` headers. In production, you may see multiple keys; select the one whose `kid` matches the JWT header.

---
## Decoded Payload Example

```json
{
  "cur": "AED",
  "stat": "CAPTURED",
  "pacc": 85,
  "vpa": 1.5,
  "iss": "https://api.pointspay.com/v4",
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
## Implementation Examples

Production-ready code examples following JWT.IO standards for different languages.

### Python (PyJWT + cryptography)

**Requirements**: `pip install PyJWT>=2.8.0 cryptography>=41.0.0 requests>=2.31.0`

This implementation follows JWT.IO standards with:
- ✅ Automatic OIDC discovery for JWKS endpoint
- ✅ Dynamic audience support (per-client/merchant)
- ✅ Algorithm enforcement (RS256/RS384/RS512)
- ✅ Full claims validation (iss, aud, exp, iat)
- ✅ Key rotation support via `kid` matching

```python
"""
JWT Signature Verification for PointsPay API

This module provides production-ready JWT verification with dynamic audience support.
Each client/merchant has their unique audience identifier for secure token validation.
"""

import base64
import json
from typing import Any, Dict

import jwt as pyjwt
import requests
from cryptography.hazmat.primitives.asymmetric import rsa


def _decode_jwt_part(part: str) -> Dict[str, Any]:
    """Decode a JWT part (header or payload) with proper padding."""
    part += '=' * (4 - len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(part))


def _extract_token_metadata(token: str) -> tuple[str, str, str]:
    """Extract issuer, key ID, and algorithm from token."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid JWT token format")
    
    header = _decode_jwt_part(parts[0])
    payload = _decode_jwt_part(parts[1])
    
    issuer = payload.get('iss')
    key_id = header.get('kid')
    algorithm = header.get('alg')
    
    if not all([issuer, key_id, algorithm]):
        raise ValueError("Token missing required metadata (iss, kid, or alg)")
    
    return str(issuer), str(key_id), str(algorithm)


def _fetch_jwks_uri(issuer: str) -> str:
    """Fetch JWKS URI from OpenID Connect discovery endpoint."""
    discovery_url = f"{issuer}/.well-known/openid-configuration"
    response = requests.get(discovery_url, timeout=10)
    response.raise_for_status()
    return response.json()['jwks_uri']


def _fetch_signing_key(jwks_uri: str, key_id: str) -> Dict[str, Any]:
    """Fetch the specific signing key from JWKS."""
    response = requests.get(jwks_uri, timeout=10)
    response.raise_for_status()
    jwks = response.json()
    
    for key in jwks.get('keys', []):
        if key.get('kid') == key_id:
            return key
    
    raise ValueError(f"Signing key '{key_id}' not found in JWKS")


def _jwk_to_rsa_public_key(jwk: Dict[str, Any]) -> Any:
    """Convert JWK to RSA public key."""
    n_bytes = base64.urlsafe_b64decode(str(jwk['n']) + '==')
    e_bytes = base64.urlsafe_b64decode(str(jwk['e']) + '==')
    n = int.from_bytes(n_bytes, 'big')
    e = int.from_bytes(e_bytes, 'big')
    return rsa.RSAPublicNumbers(e, n).public_key()


def _get_public_key(issuer: str, key_id: str) -> Any:
    """Retrieve the public key for signature verification."""
    jwks_uri = _fetch_jwks_uri(issuer)
    signing_key = _fetch_signing_key(jwks_uri, key_id)
    return _jwk_to_rsa_public_key(signing_key)


def verify_pointspay_token(
    token: str,
    audience: str,
    verify_expiration: bool = True
) -> Dict[str, Any]:
    """
    Verify a PointsPay JWT token following JWT.IO standards.
    
    Args:
        token: JWT token from PointsPay API
        audience: Your unique client/merchant identifier
        verify_expiration: Whether to verify token hasn't expired (default: True)
        
    Returns:
        Dict containing decoded payment information:
            - oid: Order ID
            - amt: Payment amount
            - cur: Currency code
            - stat: Payment status
            - iss: Issuer
            - aud: Audience
            - exp: Expiration timestamp
            - iat: Issued at timestamp
            
    Raises:
        ValueError: Invalid token format or missing required metadata
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidAudienceError: Audience doesn't match
        jwt.InvalidIssuerError: Issuer doesn't match
        jwt.InvalidSignatureError: Signature verification failed
    """
    issuer, key_id, algorithm = _extract_token_metadata(token)
    public_key = _get_public_key(issuer, key_id)
    
    return pyjwt.decode(
        token,
        public_key,
        algorithms=[algorithm],
        audience=audience,
        issuer=issuer,
        options={"verify_exp": verify_expiration}
    )


# Example usage
if __name__ == "__main__":
    AUDIENCE = "YOUR_CLIENT_ID"  # Replace with your actual client/merchant ID
    payment_token = "eyJhbGc..."  # Replace with actual token from PointsPay
    
    try:
        payload = verify_pointspay_token(
            token=payment_token, 
            audience=AUDIENCE,
			verify_expiration=True
        )
        print(f"✓ Token valid")
        print(f"Order: {payload['oid']}, Amount: {payload['amt']} {payload['cur']}")
        print(f"Status: {payload['stat']}")
    except Exception as e:
        print(f"✗ Verification failed: {e}")
```

---
### JavaScript (Node.js, using jose)

**Installation**: `npm install jose`

---
### JavaScript (Node.js, using jose)

**Installation**: `npm install jose`

```js
import { createRemoteJWKSet, jwtVerify, decodeProtectedHeader } from 'jose';

const JWKS_URL = 'https://{yourDomain}/.well-known/jwks.json';
const EXPECTED_ISS = 'https://api.pointspay.com/v4';  // Issuer is a URL
const EXPECTED_AUD = 'your-audience-here';
const ALLOWED_ALGORITHMS = ['RS256', 'RS384', 'RS512'];

// Create a cached remote JWK set fetcher
const jwks = createRemoteJWKSet(new URL(JWKS_URL));

async function verifyToken(token) {
  // Extract and validate algorithm from token header
  const header = decodeProtectedHeader(token);
  const algorithm = header.alg;
  
  if (!ALLOWED_ALGORITHMS.includes(algorithm)) {
    throw new Error(`Unsupported algorithm: ${algorithm}`);
  }
  
  const { payload, protectedHeader } = await jwtVerify(token, jwks, {
    issuer: EXPECTED_ISS,
    audience: EXPECTED_AUD,
    algorithms: [algorithm],  // Use algorithm from token header
  });
  
  // Additional business validations
  if (payload.stat !== 'CAPTURED') throw new Error('Unexpected status');
  return payload;
}

// Demo usage (replace with the live token you receive):
const demoToken = 'eyJhbGciOiJSUzI1NiIsImtpZCI6InBwLWRlbW8ta2V5LTEiLCJ0eXAiOiJKV1QifQ.eyJjdXIiOiJBRUQiLCJzdGF0IjoiQ0FQVFVSRUQiLCJwYWNjIjo4NSwidnBhIjoxLjUsImlzcyI6InBvaW50c3BheSIsImFtdCI6MTEyNTAsInBpZCI6IjI3MWQyZjMyZmNiZjQzMDA4MGNhYjE2ZDY4MTBjOGNjIiwib2lkIjoiMzkiLCJub25jZSI6IjJmYmNhMzZjLTBjOWEtNDc3MC05N2QwLWUzZTBkNGJlNzlhOSIsImF1ZCI6InlvdXItYXVkaWVuY2UtaGVyZSIsInByZWQiOjAsInZwciI6MC43MywiaWF0IjoxNzU5NDg5MTM0LCJleHAiOjE3NTk0ODk3MzR9.HE3I660wzQVgUtzsc7LKFIBdEx9w-G1TrLRTB3Y8PyvV-q1S7kwau252TowZYTuraUqDfEpqMsDcEJusUMJ_RIE0-2rLk1Su_shpzBT271nX9EZoAQLPbgE75gKe0e4Sb0z37Jb2uQXvWRRhiTiOlFAxG06TC2vs0usO9Kpuu_fZhBgSVbx_CXE8HC3Zj0cKkkm8z8Y-MhqdFwZVOxxo40joojMlZBCMB6RaIEZ6ebk-fMOBDy0iSc8UV7iDWJJJBnMaEbaSVpI83-i6C0ltY93pYxotcoQL0UaWFNYf0fR1WxNHNJzIDFpjPZ0XU9iArN8fEFoJ_ruOYdqNOJfLRQ';
verifyToken(demoToken).then(p => console.log('Valid payload', p)).catch(e => console.error('Invalid', e));
```

---
### PHP (firebase/php-jwt)

**Installation**: `composer require firebase/php-jwt`

```php
<?php
require 'vendor/autoload.php';

use Firebase\JWT\JWT;
use Firebase\JWT\Key;
use phpseclib3\Math\BigInteger;
use phpseclib3\Crypt\RSA;

$JWKS_URL = 'https://{pointspay_domain}/.well-known/jwks.json';
$EXPECTED_ISS = 'https://api.pointspay.com/v4';  // Issuer is a URL
$EXPECTED_AUD = 'your-audience-here';
$ALLOWED_ALGORITHMS = ['RS256', 'RS384', 'RS512'];

$token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6InBwLWRlbW8ta2V5LTEiLCJ0eXAiOiJKV1QifQ...';

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

    $rsa = RSA::loadPublicKey(['n' => $n, 'e' => $e]);
    return $rsa->toString('PKCS8');
}

// Parse header and extract algorithm
$parts = explode('.', $token);
if (count($parts) !== 3) throw new RuntimeException('Malformed token');
$header = JWT::jsonDecode(JWT::urlsafeB64Decode($parts[0]));

// Validate algorithm from token header
$algorithm = $header->alg ?? null;
if (!in_array($algorithm, $ALLOWED_ALGORITHMS, true)) {
    throw new RuntimeException("Unsupported algorithm: $algorithm");
}

$kid = $header->kid ?? null;
if (!$kid) throw new RuntimeException('Missing kid');

// Fetch JWKS & locate key
$jwks = json_decode(file_get_contents($JWKS_URL), true, flags: JSON_THROW_ON_ERROR);
$jwk = null;
foreach ($jwks['keys'] as $k) {
    if (($k['kid'] ?? null) === $kid) {
        $jwk = $k;
        break;
    }
}
if (!$jwk) throw new RuntimeException('kid not found in JWKS');

// Build PEM & verify using algorithm from token header
$publicKey = jwk_to_pem($jwk);
$claims = JWT::decode($token, new Key($publicKey, $algorithm));

// Claim validation
if (($claims->iss ?? null) !== $EXPECTED_ISS) throw new RuntimeException('Bad iss');
$aud = $claims->aud ?? null;
$audList = is_array($aud) ? $aud : [$aud];
if (!in_array($EXPECTED_AUD, $audList, true)) throw new RuntimeException('Bad aud');

var_dump($claims); // Valid
```

---
### Java (Nimbus JOSE + JWT)

**Installation**: Add Maven dependency:

```xml
<dependency>
  <groupId>com.nimbusds</groupId>
  <artifactId>nimbus-jose-jwt</artifactId>
  <version>9.37.3</version>
</dependency>
```

**Code**:

```java
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.jwk.source.RemoteJWKSet;
import com.nimbusds.jose.proc.*;
import com.nimbusds.jwt.SignedJWT;
import com.nimbusds.jwt.proc.*;

import java.net.URL;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public class JwtVerifier {
    private static final String JWKS_URL = "https://{yourDomain}/.well-known/jwks.json";
    private static final String EXPECTED_ISS = "https://api.pointspay.com/v4";
    private static final String EXPECTED_AUD = "your-audience-here";
    private static final Set<JWSAlgorithm> ALLOWED_ALGORITHMS = new HashSet<>(Arrays.asList(
        JWSAlgorithm.RS256, JWSAlgorithm.RS384, JWSAlgorithm.RS512
    ));

    public static void main(String[] args) throws Exception {
        String token = "eyJhbGciOiJSUzI1NiIsImtpZCI6InBwLWRlbW8ta2V5LTEiLCJ0eXAiOiJKV1QifQ...";

        // Parse token and extract algorithm from header
        SignedJWT jwt = SignedJWT.parse(token);
        JWSAlgorithm algorithm = jwt.getHeader().getAlgorithm();
        
        // Validate algorithm from token header
        if (!ALLOWED_ALGORITHMS.contains(algorithm)) {
            throw new IllegalStateException("Unsupported algorithm: " + algorithm);
        }

        // Use the algorithm from token header for verification
        RemoteJWKSet<?> jwkSet = new RemoteJWKSet<>(new URL(JWKS_URL));
        ConfigurableJWTProcessor<?> processor = new DefaultJWTProcessor<>();
        JWSKeySelector<?> keySelector = new JWSVerificationKeySelector<>(algorithm, jwkSet);
        processor.setJWSKeySelector(keySelector);

        JWTClaimsSetVerifier<?> claimsVerifier = (claims, context) -> {
            if (!EXPECTED_ISS.equals(claims.getIssuer())) 
                throw new BadJWTException("Bad iss");
            if (claims.getAudience() == null || !claims.getAudience().contains(EXPECTED_AUD)) 
                throw new BadJWTException("Bad aud");
        };
        processor.setJWTClaimsSetVerifier(claimsVerifier);

        processor.process(jwt, null); // If no exception, token is valid
        System.out.println("Token valid. amt=" + jwt.getJWTClaimsSet().getLongClaim("amt"));
    }
}
```

---
## Common Pitfalls & JWT.IO Best Practices

Following JWT.IO standards helps avoid these common security issues:

| Issue | Explanation | JWT.IO Standard Fix |
|-------|-------------|---------------------|
| **Algorithm confusion** | Token header says RS256 but code allows HS256 | ✅ Explicitly whitelist RS256/RS384/RS512 only - never trust header `alg` |
| **Key rotation issues** | New key appears, old one removed | ✅ Cache JWKS with TTL; refetch on `kid` miss; support multiple active keys |
| **Clock skew** | Minor diff in server times fails exp/iat | ✅ Allow small leeway (e.g. 60s) per JWT spec |
| **Missing audience check** | Any site could reuse token | ✅ Enforce exact expected audience per client/merchant |
| **Expired tokens accepted** | Missing exp validation | ✅ Use library options to require `exp` and validate it |
| **Issuer not validated** | Token from wrong source accepted | ✅ Validate `iss` claim matches PointsPay issuer URL (e.g., `https://api.pointspay.com/v4`) |
| **Missing required claims** | Token lacks critical claims | ✅ Require `iss`, `aud`, `exp`, `iat` per OIDC/JWT standards |

---
## Additional Resources

- **JWT.IO**: https://jwt.io - Interactive JWT debugger and documentation
- **RFC 7519**: https://tools.ietf.org/html/rfc7519 - JSON Web Token standard
- **OpenID Connect Discovery**: https://openid.net/specs/openid-connect-discovery-1_0.html
- **PointsPay API Documentation**: Contact your integration manager for full API docs