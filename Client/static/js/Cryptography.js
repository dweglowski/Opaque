export {CryptographyController};

class CryptographyController {

    /* Logic for all encryption, decryption and key generation */


    // Store master key for client (generated from password) to decrypt other keys
    #master_key = null;

    // Used for encrypting websocket connection
    #EncryptionInTransitClientPublicKey = null;
    #EncryptionInTransitClientPrivateKey = null;
    #EncryptionInTransitServerPublicKey = null;

    // Direct messaging end-to-end encryption keys
    #DirectMessagingE2EClientPublicKey = null;
    #DirectMessagingE2EClientPrivateKey = null;

    // Analytics encryption keys
    #AnalyticsEncryptionClientPublicKey = null;
    #AnalyticsEncryptionClientPrivateKey = null;
    
    
    /** Hashes the password before it is sent to the server, uses PBKDF2 for security */
    async hash(password, salt){
        var iterations = 500_000;
        var hash = 'SHA-256';
        var length = 64;

        var enc = new TextEncoder();
        var key = await crypto.subtle.importKey(
            'raw',
            enc.encode(password),
            'PBKDF2',
            false,
            ['deriveBits']
        );
        
        enc = new TextEncoder();
        var hash = await crypto.subtle.deriveBits(
          { name: 'PBKDF2', hash: hash, salt: enc.encode(salt), iterations : iterations },
          key,
          length * 8
        )

        return btoa(String.fromCharCode(...new Uint8Array(hash)));
    }

    /** Generates the salt for a new user */
    hash_generate_salt() {
        var salt = crypto.getRandomValues(new Uint8Array(32));
        return btoa(String.fromCharCode(...salt));
    }
    

    /** Loads the master key, generated from the user's password, used to decrypt other keys */
    async load_master_key(password, salt){
        this.#master_key = await this.#derive_encryption_key_from_password(password, salt);
    }

    async #derive_encryption_key_from_password(password, salt) {

        var enc = new TextEncoder();
        const base = await window.crypto.subtle.importKey(
            "raw",
            enc.encode(password),
            { name: "PBKDF2" },
            false,
            ["deriveKey"]
        );


        enc = new TextEncoder();
        return await window.crypto.subtle.deriveKey(
            {
                name: "PBKDF2",
                hash: "SHA-256",
                salt: enc.encode(salt),
                iterations: 400_000
            },
            base,
            {name: "AES-GCM", length: 256},
            false,
            ["encrypt", "decrypt"]
        );
    }

    async #encrypt_key_with_master_key(key) {
        const iv = crypto.getRandomValues(new Uint8Array(12));  // Initialization vector, means that identical messages have different ciphertexts, required for js's crypto library

        var enc = new TextEncoder();
        var ciphertext = await crypto.subtle.encrypt(
            { name: "AES-GCM", iv },
            this.#master_key,
            enc.encode(key)
        );

        var ciphertext_str = btoa(String.fromCharCode(...new Uint8Array(ciphertext)));
        var iv_str = btoa(String.fromCharCode(...iv));

        return iv_str + ciphertext_str;
    }

    async #decrypt_key_with_master_key(encrypted_key) {
        // Extract iv from ciphertext
        var iv_str = encrypted_key.slice(0, 16);
        var ciphertext_str = encrypted_key.slice(16);

        var iv = Uint8Array.from(atob(iv_str), c => c.charCodeAt(0));
        var ciphertext = Uint8Array.from(atob(ciphertext_str), c => c.charCodeAt(0));

        var decrypted = await crypto.subtle.decrypt(
            { name: "AES-GCM", iv },
            this.#master_key,
            ciphertext
        );

        return String.fromCharCode(...new Uint8Array(decrypted));
    }
    



}
