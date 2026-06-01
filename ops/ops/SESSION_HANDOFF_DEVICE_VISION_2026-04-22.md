# SLH DEVICE + BLOCKCHAIN VISION (2026)

## Core Idea
ESP32 devices become hardware-secured identity nodes inside the SLH ecosystem.

Each device acts as both a cryptographic authority and a physical approval layer.

---

## Strategic Goal
Transform the ESP32 device layer from a simple display/controller into a trusted hardware extension of:
- SLH API
- Control Layer
- Telegram Guardian
- Wallet / approvals
- Future blockchain audit and provisioning pipeline

---

## 1. Device Proof of Authenticity
- Hardware serial / chip ID becomes the device identity root
- Device identity is hashed and registered on-chain
- Public key is bound to the device record
- Firmware can validate whether it is running on the expected device

Value:
- Verify genuine devices
- Detect cloning
- Prevent unauthorized firmware duplication
- Establish a trust anchor for field devices

---

## 2. Physical Transaction Approval (Hardware 2FA)
Critical actions should require physical approval on the device:
- wallet transfers
- admin confirmations
- guardian security actions
- sensitive configuration changes

Flow:
User request -> backend challenge -> device button press -> device signature -> backend verification

---

## 3. Immutable OTA
OTA must be approval-based and hash-verified:
- firmware hash registered in SLH trust layer
- device downloads candidate update
- device validates hash/signature
- mismatch triggers SAFE MODE + alerting

---

## 4. Kosher / Restricted Mode Capabilities
Potential device-specialized flows:
- time-gated operation modes
- Shabbat-safe behavior presets
- community / Gemach terminal workflows
- limited UI for approved device actions only

---

## 5. Hardware Participation Layer
A connected device can become a measurable ecosystem participant:
- uptime reputation
- device presence / contribution score
- staking / points / token incentives
- real-time leaderboard display

---

## 6. Provisioning Pipeline
Future automation target: slh-provision.ps1

Desired stages:
1. detect connected ESP32
2. read hardware unique identifier
3. generate device keypair
4. encrypt and store provisioning bundle
5. register device public identity
6. bind device to user/account
7. flash firmware profile
8. record provisioning event in audit trail

---

## Architecture Mapping
DEVICE (ESP32)
-> SLH API
-> CONTROL LAYER
-> TELEGRAM / GUARDIAN
-> BLOCKCHAIN TRUST LAYER (future)
-> AUDIT / REPORTING

---

## Current Status
- Device boot confirmed
- WiFi confirmed
- TFT configuration corrected to ILI9341 driver
- Firmware build path partially stabilized
- Firmware source selection still needs cleanup
- Blockchain / provisioning layer not implemented yet

---

## Immediate Next Steps
1. restore a single valid firmware entrypoint in src
2. bring display to stable live state
3. build system_bridge.py
4. connect device to API / Guardian flows
5. define device registry schema
6. design smart contract / on-chain registry

---

## Long-Term Outcome
SLH devices become trusted physical endpoints for approvals, identity, monitoring, and secure ecosystem participation.


[FEATURE_BLOCK] DEVICE_IDENTITY_LAYER
