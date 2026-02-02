# Image Steganography Project 🕵️‍♂️✨

**Yo what's up guys! Welcome to my Image Steganography Project.**  
Yeh mera college ka project hai, and honestly, scene bohot crazy hai. Basically, hum images ke andar secret messages chupayenge, like actual spy stuff! 😎

Agar tum bhi "Freshie" ho aur soch rahe ho ki "Bhai yeh kya chal raha hai?", tension mat lo. Main sab kuch explain karunga, ekdum simple language mein. No heavy jargon, just pure logic aur thoda sa "jugaad".

Let's dive in! 🚀

---

## 🧐 What is Steganography? (Basics)

Socho tume apne best friend ko ek secret message bhejna hai, but teacher (ya parents 😜) aas-paas hain. Tum kya karoge?  
Tum us message ko kisi aisi cheez mein chupa doge jo ekdum normal dikhe via.  

**Steganography** wahi hai!
It is the art of hiding data within data. Humara message (text) ek innocent-looking image ke andar chupa hota hai.  
*Kisi ko pata bhi nahi chalega ki photo ke peeche raaz chupa hai!* 🤫

---

## 🧠 The Concepts (Thoda Technical, but Easy)

Humne is project mein 3 main techniques use ki hain taaki security next level ho jaye via. Samjho kaise:

### 1. Huffman Coding 📦 (Making it SMOL)
Sabse pehle, humare message ko compress karna padta hai.  
Imagine karo tumhara message ek bada sa suitcase hai. Huffman coding usko vacuum seal karke ek chote se pouch mein convert kar deta hai.
*   **Why?** Kyunki image ke paas limited space hoti hai. Jitna chota message, utna easy hiding.
*   **How?** Jo letters baar-baar aate hain (like 'a', 'e'), unko chota code milta hai. Jo kam aate hain (like 'z'), unko bada. *Smart stuff, right?*

### 2. Spread Spectrum 🌊 (Faila Do!)
Ab chupaana hai, toh ek jagah mat rakho.  
Spread Spectrum technique humare message ke bits ko randomly poori image mein faila (spread) deta hai.
*   **Vibe:** Jaise bread pe jam spread karte hain, waise hi hum bits spread karte hain.
*   **Fayda:** Agar koi hacker image ka ek part dekhega, toh use kuch samajh nahi aayega. Sab kuch scattered hai!

### 3. LSB (Least Significant Bit) 🖼️ (The Real Magic)
Yeh sabse important part hai. Dhyan se suno! 👂
Har image pixels se banti hai (Red, Green, Blue). Har pixel ki ek numeric value hoti hai (0-255).
Computer mein yeh numbers binary (0s and 1s) mein hote hain. Example: `10010110`.

*   **LSB (Last Wala Bit):** Jo last digit hai (Rightmost), usko agar hum change kar dein, toh color mein itna minor difference aata hai ki human eye pakad hi nahi sakti.
*   **Hack:** Hum apne secret message ke bits ko image ke pixels ke LSB mein daal dete hain.
    *   Original: `1001011`**`0`** (Dark Red)
    *   Modified: `1001011`**`1`** (Still Dark Red, but ab isme humara data hai!)

---

## 🛠️ The Tech Stack (Humne kya use kiya?)

*   **Python:** Kyunki Python hai toh mumkin hai. 🐍
*   **Flask:** Website banane ke liye backend framework.
*   **HTML/CSS/JS:** Frontend chamkane ke liye. (Humne glassmorphism use kiya hai, looks premium bro! ✨)
*   **NumPy:** Numbers ke saath khelne ke liye (Matrix calculations for images).
*   **Pillow (PIL):** Image processing ke liye.

---

## 🚀 How to Run This? (Chalao kaise?)

Follow these steps mere bhai:

1.  **Terminal kholo** (woh black screen hacker wali).
2.  **Project folder mein jao**.
3.  **Virtual Environment banao** (Taaki system mess up na ho):
    ```bash
    python3 -m venv venv
    ```
4.  **Activate karo**:
    ```bash
    source venv/bin/activate  # Mac/Linux
    # ya phir Windows ke liye: venv\Scripts\activate
    ```
5.  **Dependencies install karo**:
    ```bash
    pip install -r requirements.txt
    ```
6.  **Server Start karo**:
    ```bash
    python app.py
    ```
7.  **Browser mein jao**: Open `http://127.0.0.1:5000`.

Bhoom! 💥 Website load ho jayegi.
Encode tab mein jao, image dalo, message likho, aur magic dekho!

---

## ⚠️ Important Note (Dhyan rakhna!)
Currently, hum encryption keys (Huffman Trees) server ki memory mein store kar rahe hain.
Iska matlab: **Agar server restart kiya, toh purani images decode nahi hongi.**
Yeh sirf ek demo project hai, toh chill hai. But production mein hum database use karte.

---

Enjoy the project guys! Koi doubt ho toh pooch lena.
Keep coding, keep rocking! 🤘💻
