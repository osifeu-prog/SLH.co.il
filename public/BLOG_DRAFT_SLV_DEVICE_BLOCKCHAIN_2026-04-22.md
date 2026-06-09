# SLH Device Vision: From ESP32 Control Panel to Trusted Hardware Node

The SLH device layer is evolving beyond a screen-and-buttons interface.

The direction is to turn ESP32-based devices into trusted hardware nodes that can:
- prove authenticity
- approve sensitive actions physically
- validate OTA integrity
- participate in the wider SLH trust and control architecture

## Why this matters
A hardware-backed approval and identity layer can strengthen:
- wallet operations
- guardian security flows
- auditability
- anti-cloning protections
- future provisioning and blockchain registration

## Roadmap themes
- device authenticity
- hardware 2FA
- immutable OTA
- restricted / kosher device modes
- provisioning pipeline
- participation / reputation layer

## Current state
The firmware and display stack are being stabilized first. Once the device runtime is stable, provisioning, bridge logic, and blockchain registration can be added safely.
