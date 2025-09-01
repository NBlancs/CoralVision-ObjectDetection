# 🌊 CoralVision Django

**CoralVision Django** is a web application built with **Django** for object detection using **YOLOv5**.  
It allows you to interact with real-time video streams, apply object detection models, view predictions, and more.

---

## ✨ Features
- 🔍 Real-time object detection using the YOLO model  
- 🌐 Web-based interface built with Django for easy interaction  
- ⚡ Easy setup with a pre-configured database and migrations  
- 🛠️ Admin panel for managing the application  

---

## 📋 Requirements
- Python **3.x**  
- Django **5.2+**  
- Other Python dependencies (listed in `requirements.txt`)  

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/CoralVision.git
cd CoralVision
```

### 2. Set up a Virtual Environment
```bash
python -m venv .venv
```

Activate the virtual environment:

**On Windows:**
```bash
.venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r CoralVision-Django/requirements.txt
```

### 4. Set up the Database
```bash
cd CoralVision-Django/django_site
python manage.py migrate
```

### 5. Start the Django Development Server
```bash
python manage.py runserver
```

Your application will be available at:  
👉 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 6. Create a Superuser (Optional)
To access the Django admin panel:
```bash
python manage.py createsuperuser
```

Then log in at 👉 [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🚀 Usage
- Run the server and navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  
- Upload videos for object detection, or stream live video (depending on configuration)  
- Use the Django admin panel to manage the database, users, and models  

---

## 🐞 Troubleshooting
- **Error: `manage.py` not found**  
  Ensure you're in the correct directory:  
  `CoralVision-Django/django_site`

- **Error: Server not running**  
  Check terminal error messages and review settings in:  
  `coral_site/settings.py`

---
