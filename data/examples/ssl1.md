### [Product Announcement] Notice on Shortened Validity Period for SSL Certificates  
Dear BytePlus Users,  
As per the latest voting results from the CA/B Forum (Proposal [SC-081v3](https://cabforum.org/2025/04/11/ballot-sc081v3-introduce-schedule-of-reducing-validity-and-data-reuse-periods)), in order to further enhance the security of network communications, the maximum validity period for SSL/TLS certificates worldwide will be gradually shortened. In line with this industry standard and considering the specific implementation strategies of certificate authorities, the BytePlus Certificate Center will adjust its relevant SSL certificate validity policies accordingly.  
> The CA/B Forum (Certification Authority/Browser Forum) is the authoritative standards organization in the global digital certificate industry. Any SSL/TLS certificate that aims to gain public trust from mainstream browsers and operating systems must comply with the baseline requirements established by the CA/B Forum.  
## Key Changes  
Starting from 2026, the maximum validity period for SSL/TLS certificates will be phased down from the current 398 days (approximately 13 months) to 47 days. This adjustment is designed to reduce risks arising from security incidents such as private key leaks by increasing the frequency of certificate renewals.  
The specific schedule for validity period changes is as follows:  
:::tip  
The actual validity period of a certificate is subject to the execution rules of the specific certificate authority and the information displayed on the purchase page.  
:::  
| Issued On or After | Issued Before | Maximum SSL Certificate Validity Period |  
| :--- | :--- | :--- |  
| — | March 15, 2026 | 398 days |  
| March 15, 2026 | March 15, 2027 | 200 days |  
| March 15, 2027 | March 15, 2029 | 100 days |  
| March 15, 2029 | — | 47 days |  
:::tip  
According to the [official DigiCert announcement](https://knowledge.digicert.com/alerts/public-tls-certificates-199-day-validity), starting February 24, 2026, DigiCert will stop issuing public SSL/TLS certificates with a validity period exceeding 199 days. This policy applies to DigiCert’s DV/OV/EV and other public TLS certificate products. The implementation strategy is based on the CA/B Forum’s requirement for a phased cap of 200 days, and under compliance and security considerations, 199 days has been adopted as the practical issuance limit.  
:::  
## Impact on You  
With the gradual shortening of certificate validity periods, you will need to perform certificate renewal and deployment operations more frequently to ensure your business continues to use valid SSL/TLS certificates and avoid access anomalies or service interruptions caused by expired certificates.  
## Recommended Actions  
To prepare for this change, we strongly recommend that you:  
* Embrace automation: Manually managing certificate renewals and deployments will become increasingly challenging. We suggest that you adopt automated certificate management tools as soon as possible to simplify the management process and reduce the risk of operational errors.  
The BytePlus Certificate Center will continue to optimize its certificate automation capabilities to provide you with even more convenient services.  
* Stay informed: We will closely monitor the latest developments from the CA/B Forum and promptly share relevant information with you.  
The BytePlus Certificate Center is committed to providing you with secure and reliable certificate services. If you have any questions about this change or certificate management, please feel free to contact us at any time.  
Thank you for your trust and support of BytePlus!