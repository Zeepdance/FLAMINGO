FLAMINGO – Multispectral Scanner for Cultural Heritage
FLAMINGO is a low‑cost, open‑source multispectral imaging system designed for non‑invasive analysis of cultural heritage objects. It reveals hidden text, erased inscriptions, forgery traces, and luminescent security features that are invisible to the naked eye.

🦩 Overview
FLAMINGO captures images of the same object in three spectral ranges:

Visible Light – reference image

Ultraviolet (UV) – reveals luminescent details (security features, restoration traces)

Infrared (IR) – penetrates surface layers to read blacked‑out or faded text

The system is built from widely available components, costs less than $300, and is fully open source. It makes professional‑grade multispectral analysis accessible to museums, archives, schools, and volunteers.

🔧 How It Works
Camera Modification – An ESP32‑S3‑CAM module has its built‑in IR‑cut filter physically removed, making the sensor sensitive to UV and IR light.

Controlled Illumination – UV (365 nm) and IR (850 nm) LED arrays are switched via MOSFETs, controlled by an ESP32 microcontroller.

Image Capture – The system captures three images of the same object (Visible, UV, IR) with fixed manual camera settings (AWB, AEC, AGC disabled) to eliminate artefacts.

Analysis – Comparing the three channels reveals hidden information: IR penetrates stains and markers, while UV highlights luminescent materials.

📷 Hardware Components
Component	Description
Camera	ESP32‑S3‑CAM (IR‑cut filter removed)
UV Light	365 nm LED matrix
IR Light	850 nm high‑power LED
Controller	ESP32 (orchestrates illumination and capture)
Motion System	2× NEMA17 stepper motors + DRV8825 drivers + CNC Shield V3
Motion Control	Arduino Uno running GRBL firmware
Enclosure	Custom‑designed, 3D‑printed and CNC‑machined (wood + aluminium)
Total Cost	< $300
🧪 Validation & Results
We tested FLAMINGO on a document with multiple layers of marker ink, paint, and stains – completely unreadable to the human eye.

Visible Light – only dark blotches visible, text unreadable

UV Light – weak luminescence, text still unreadable

IR Light – surface layers become transparent, text appears clearly readable

Conclusion: FLAMINGO successfully recovers information that is invisible in normal light.

🌍 Social Impact
Accessibility – 10–20× cheaper than professional systems ($300 vs. $5,000+)

Non‑invasive – uses only light, no chemicals or physical contact

Education – STEM learning tool for optics, robotics, and programming

Open Source – all schematics, code, and 3D models are publicly available

FLAMINGO aligns with the UN Sustainable Development Goals:

SDG 4 – Quality Education

SDG 9 – Industry, Innovation and Infrastructure

SDG 11 – Sustainable Cities and Communities (cultural heritage preservation)

🚀 Future Plans
Fully autonomous 3‑axis scanning with GRBL control

AI‑powered text recognition and enhancement

Upgrade to Raspberry Pi camera for higher resolution

Partnership with local museums for real‑world testing

Full open‑source release on GitHub (schematics, code, 3D models, guide)

📁 Repository Structure
text
flamingo/
├── docs/               # Documentation and user manual
├── hardware/           # Schematics, PCB designs, 3D models
├── firmware/           # ESP32-CAM code, GRBL config
├── software/           # Image processing scripts
├── tests/              # Test images and results
└── README.md           # This file
🤝 Team
Team Veltrix – Kazakhstan

Project developed at MIT FabLab, Satbayev University with support from university engineers and access to professional fabrication equipment.

📄 License
This project is open source. Hardware designs are licensed under CERN OHL‑S, software under MIT License.
