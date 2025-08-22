Domain: gwanalytica.ai
Static IP: 34.107.218.194
Type: Global External IPv4 (Google Cloud)
Attached to: HTTPS LB → Cloud Run service

---

# 🌐 Domain Runbook – gwanalytica.ai

## 1. Domain Registrar

* **Registrar:** GoDaddy
* **Domain:** gwanalytica.ai
* **Where to manage DNS:**
  GoDaddy → Profile → *My Products* → gwanalytica.ai → *Manage DNS*

---

## 2. Google Cloud Setup

### Static IP

* **Name in GCP:** `gwanalytica-ip`
* **Type:** Global External IPv4
* **Where to view:**
  GCP Console → VPC Network → IP Addresses
  or via CLI:

  ```bash
  gcloud compute addresses describe gwanalytica-ip --global --format="get(address)"
  ```

### Cloud Run Service

* **Service Name:** `YOUR_SERVICE`
* **Region:** `YOUR_REGION`

---

## 3. Load Balancer (Application LB)

* **Backend:** Serverless NEG → Cloud Run service (`YOUR_SERVICE`, `YOUR_REGION`)
* **Backend Service Name:** `gwanalytica-backend`
* **URL Map:** `gwanalytica-map`
* **Target Proxy:** `gwanalytica-proxy`
* **Forwarding Rule:** `gwanalytica-https-rule` (port 443 → static IP)

---

## 4. SSL / HTTPS

* **Certificate Type:** Google-managed
* **Cert Name:** `gwanalytica-cert`
* **Domains Covered:**

  * gwanalytica.ai
  * [www.gwanalytica.ai](http://www.gwanalytica.ai)
* **Renewal:** Automatic (Google-managed)

---

## 5. DNS Records @ GoDaddy

| Type  | Name | Value              | TTL  | Notes             |
| ----- | ---- | ------------------ | ---- | ----------------- |
| A     | @    | `<your static IP>` | 1 hr | Root domain → LB  |
| CNAME | www  | gwanalytica.ai     | 1 hr | www → root domain |

⚠️ Make sure only **one** record exists for `www` (delete any conflicting A-records).

---

## 6. Optional: HTTP → HTTPS Redirect

If you want plain `http://` requests to auto-upgrade:

* Add an **HTTP (port 80) forwarding rule** in the LB, pointing to a URL map that redirects → HTTPS.
* Google’s docs: [Redirecting HTTP to HTTPS](https://cloud.google.com/load-balancing/docs/https/https-redirect)

---

## 7. Where to Check Things

* **IP health:**
  `ping gwanalytica.ai` (should resolve to your static IP)
* **Cert status:**
  GCP Console → Network Services → Certificates
* **LB status:**
  GCP Console → Network Services → Load balancing
* **DNS propagation:**
  [whatsmydns.net](https://whatsmydns.net) → enter gwanalytica.ai

---

## 8. Recovery Notes

* If DNS fails → check GoDaddy records.
* If HTTPS fails → check SSL certificate status in GCP.
* If traffic fails → verify NEG points to the right Cloud Run service/region.
* Never delete `gwanalytica-ip` — doing so breaks DNS.

---

Do you want me to actually **fill this in with your real service/region values** (instead of placeholders like `YOUR_SERVICE`), so it’s copy-paste ready for your notes?

