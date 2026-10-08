# MYnyak Engsel Sunset

![banner](bnr.png)

CLI client for a certain Indonesian mobile internet service provider.

# How to get environment variables
Go to [OUR TELEGRAM CHANNEL](https://t.me/alyxcli)
Copy the provided environment variables and paste them into a text file named `.env` in the same directory as `main.py`.
You can use `nano` or any text editor to create the file.

# How to run on Linux / OpenWrt

## 1. Install dependencies

### Debian / Ubuntu / Linux
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git
```

### OpenWrt
```bash
opkg update
opkg install python3 python3-pip python3-pil git
```

### Termux / Android
```bash
pkg update && pkg upgrade -y
pkg install git python python-pillow -y
```

## 2. Clone and enter the project
```bash
git clone https://github.com/flower99p/cli
cd cli
```

## 3. Install Python requirements
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## 4. Create `.env` file
```bash
cp .env.template .env
```
Then fill in the values from the provided Telegram channel.

## 5. Run the script
```bash
python3 main.py
```

# How to run with TERMUX
1. Update & Upgrade Termux
```
pkg update && pkg upgrade -y
```
2. Install Git
```
pkg install git -y
```
3. Clone this repo
```
git clone https://github.com/purplemashu/me-cli-sunset
```
4. Open the folder
```
cd me-cli-sunset
```
5. Setup
```
bash setup.sh
```
6. Run the script
```
python main.py
```

# Info

## PS for Certain Indonesian mobile internet service provider

Instead of just delisting the package from the app, ensure the user cannot purchase it.
What's the point of strong client side security when the server don't enforce it?

## Terms of Service
By using this tool, the user agrees to comply with all applicable laws and regulations and to release the developer from any and all claims arising from its use.

## Contact

contact@mashu.lol
