export {CryptographyController};

import * as paillierBigint from "https://cdn.jsdelivr.net/npm/paillier-bigint@3.4.1/+esm"; // for homomorphic encryption

class CryptographyController {

    /* Logic for all encryption, decryption and key generation */


    // Store master key for client (generated from password) to decrypt other keys
    #master_key = null;

    // Used for encrypting websocket connection
    #TlsClientPublicKey = null;
    #TlsClientPrivateKey = null;
    #TlsServerPublicKey = null;

    // Direct messaging end-to-end encryption keys
    #DirectMessagingE2EClientPublicKey = null;
    #DirectMessagingE2EClientPrivateKey = null;

    // Analytics encryption keys
    #AnalyticsEncryptionClientPublicKey = null;
    #AnalyticsEncryptionClientPrivateKey = null;
    

    /** Convert an array buffer to a base64 string */
    array_buffer_to_base64(buffer) {
        var binary = "";
        var bytes = new Uint8Array(buffer);
        for (var i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

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

        return this.array_buffer_to_base64(hash);;
    }

    /** Generates the salt for a new user */
    hash_generate_salt() {
        var salt = crypto.getRandomValues(new Uint8Array(32));
        return this.array_buffer_to_base64(salt);
    }
    

    /** Loads the master key, generated from the user's password, used to decrypt other keys */
    async load_master_key(password, salt){
        this.#master_key = await this.#derive_encryption_key_from_password(password, salt);
    }

    /** Used to turn a user password into an encryption key */
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

    /** Used to encrypt keys before storing on the server */
    async #encrypt_key_with_master_key(key) {
        const iv = crypto.getRandomValues(new Uint8Array(12));  // Initialization vector, means that identical messages have different ciphertexts, required for js's crypto library

        var enc = new TextEncoder();
        var ciphertext = await crypto.subtle.encrypt(
            { name: "AES-GCM", iv },
            this.#master_key,
            enc.encode(key)
        );

        var ciphertext_str = this.array_buffer_to_base64(ciphertext);
        var iv_str = this.array_buffer_to_base64(iv);

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

        var enc = new TextDecoder();
        return enc.decode(decrypted);
    }
    
    /** Generates keys for public key cryptography */
    async #generate_asymmetric_keys() {
        return await crypto.subtle.generateKey(
            {
                name: "RSA-OAEP",
                modulusLength: 2048,
                publicExponent: new Uint8Array([1, 0, 1]),
                hash: "SHA-256",
            },
            true,
            ["encrypt", "decrypt"]
        );
    }

    /** Encrypt data with RSA, split into blocks to allow for longer messages */
    async #encrypt_asymmetric(public_key, data) {
        
        var ciphertext = "";

        // split data into chunks of 190 characters
        var chunk_size = 190;
        
        for (var i = 0; i < data.length; i += chunk_size) {
            var chunk = data.slice(i, i + chunk_size);
            var encrypted_chunk = await this.#encrypt_chunk_asymmetric(public_key, chunk);
            ciphertext += encrypted_chunk;
        }

        return ciphertext;
    }

    /** Encrypt a chunk of data with RSA */
    async #encrypt_chunk_asymmetric(public_key, data) {
        var enc = new TextEncoder();
        var ciphertext = await crypto.subtle.encrypt(
            {
                name: "RSA-OAEP",
            },
            public_key,
            enc.encode(data)
        );
        return this.array_buffer_to_base64(ciphertext);
    }

    /** Decrypt data with RSA */
    async #decrypt_asymmetric(private_key, ciphertext) {
        var plaintext = "";

        // split ciphertext by ==
        var chunks = ciphertext.split("==").filter(chunk => chunk.length > 0);
        for (var i = 0; i < chunks.length; i++) {
            var chunk = chunks[i] + "==";
            var decrypted_chunk = await this.#decrypt_chunk_asymmetric(private_key, chunk);
            plaintext += decrypted_chunk;
        }

        return plaintext;
    }

    /** Decrypt a chunk with RSA */
    async #decrypt_chunk_asymmetric(private_key, chunk) {
        var ciphertext = Uint8Array.from(atob(chunk), c => c.charCodeAt(0));
        var decrypted = await crypto.subtle.decrypt(
            {
                name: "RSA-OAEP",
            },
            private_key,
            ciphertext
        );

        var enc = new TextDecoder();
        return enc.decode(decrypted);
    }

    /** Generates public and private keys for the websocket connection with the server. Returns the client's public key */
    async generate_tls_keys() {
        var keypair = await this.#generate_asymmetric_keys();
        this.#TlsClientPublicKey = keypair.publicKey;
        this.#TlsClientPrivateKey = keypair.privateKey;

        return this.array_buffer_to_base64(await crypto.subtle.exportKey("spki", this.#TlsClientPublicKey));
    }

    /** Remember the server's websocket public key */
    async set_tls_server_public_key(server_public_key) {
        var bytes = Uint8Array.from(atob(server_public_key), c => c.charCodeAt(0))

        this.#TlsServerPublicKey = await crypto.subtle.importKey(
            "spki",
            bytes.buffer,
            {
                name: "RSA-OAEP",
                hash: "SHA-256",
            },
            true,
            ["encrypt"]
        );
    }


    /** Generate a public private key for e2e encyrpted direct messages. Only ever called on signup. Returns public key and encrypted form of private key. */
    async generate_direct_messaging_e2e_keys() {
        var keypair = await this.#generate_asymmetric_keys();
        this.#DirectMessagingE2EClientPublicKey = keypair.publicKey;
        this.#DirectMessagingE2EClientPrivateKey = keypair.privateKey;

        var exported_public_key = await crypto.subtle.exportKey("spki", this.#DirectMessagingE2EClientPublicKey);
        var exported_private_key = await crypto.subtle.exportKey("pkcs8", this.#DirectMessagingE2EClientPrivateKey);

        var encrypted_private_key = await this.#encrypt_key_with_master_key(this.array_buffer_to_base64(exported_private_key));

        return {
            "public_key" : this.array_buffer_to_base64(exported_public_key),
            "encrypted_private_key" : encrypted_private_key
        };
    }

    /** Loads the public and private keys for e2e encrypted direct messages */
    async load_direct_messaging_e2e_keys(public_key, encrypted_private_key) {
        var private_key = await this.#decrypt_key_with_master_key(encrypted_private_key);

        var public_key_bytes = Uint8Array.from(atob(public_key), c => c.charCodeAt(0));
        var private_key_bytes = Uint8Array.from(atob(private_key), c => c.charCodeAt(0));

        this.#DirectMessagingE2EClientPublicKey = await crypto.subtle.importKey(
            "spki",
            public_key_bytes.buffer,
            {
                name: "RSA-OAEP",
                hash: "SHA-256",
            },
            true,
            ["encrypt"]
        );

        this.#DirectMessagingE2EClientPrivateKey = await crypto.subtle.importKey(
            "pkcs8",
            private_key_bytes.buffer,
            {
                name: "RSA-OAEP",
                hash: "SHA-256",
            },
            true,
            ["decrypt"]
        );
    }




    /** Encrypts the websocket data stream using the tls keys */
    async encrypt_websocket_data_tls(data) {
        return await this.#encrypt_asymmetric(this.#TlsServerPublicKey, data);
    }

    /** Decrypts the websocket data stream using the tls keys */
    async decrypt_websocket_data_tls(ciphertext) {
        return await this.#decrypt_asymmetric(this.#TlsClientPrivateKey, ciphertext);
    }


    /** Encrypts a direct message using the client's public key (sender copy of content) */
    encrypt_direct_message_sender_copy(data) {
        return this.#encrypt_asymmetric(this.#DirectMessagingE2EClientPublicKey, data);
    }

    /** Encrypts a direct message using the recipient's public key (recipient copy of content) */
    async encrypt_direct_message_recipient_copy(recipient_public_key, data) {
        var public_key_bytes = Uint8Array.from(atob(recipient_public_key), c => c.charCodeAt(0));
        var recipient_public_key = await crypto.subtle.importKey(
            "spki",
            public_key_bytes.buffer,
            {
                name: "RSA-OAEP",
                hash: "SHA-256",
            },
            true,
            ["encrypt"]
        );

        return await this.#encrypt_asymmetric(recipient_public_key, data);
    }

    /** Decrypts a direct message using the client's private key */
    decrypt_direct_message(ciphertext) {
        return this.#decrypt_asymmetric(this.#DirectMessagingE2EClientPrivateKey, ciphertext);
    }


    /** Cryptographically secure version of math.random(), produces a float between 0 and 1 */
    #secure_random() {
        // produce a random 32 bit number securely
        var array = new Uint32Array(1);
        window.crypto.getRandomValues(array);

        // convert to float between 0 and 1
        return array[0] / (2 ** 32);
    }

    /** Secure random integer between min and max */
    secure_random_int(min, max) {
        var range = max - min + 1;
        var random_float = this.#secure_random();
        return min + Math.floor(random_float * range);
    }

    /** Samples the laplace distribution to produce noise for differential privacy */
    #get_laplace_noise(scale) {
        var u = this.#secure_random() - 0.5;
        return -scale * Math.sign(u) * Math.log(1 - 2 * Math.abs(u));
    }

    /** Applies differential privacy to star score rating */
    apply_differential_privacy_to_star_score(star_score) {
        var min = 1;
        var max = 5;
        var sensitivity = (max - min);
        var epsilon = 1.8; // lower epsilon for more privacy, found 1.8 provides enough privacy while providing a good average after around 10 ratings, good for demo
        var scale = sensitivity / epsilon;

        var noise = this.#get_laplace_noise(scale);

        var noisy_star_score = star_score + noise;

        return noisy_star_score;
    }



    /** Generates keys for homomorphic encryption */
    async #generate_homomorphic_keys() {
        return await paillierBigint.generateRandomKeys(1024);
    }

    async #load_homomorphic_public_key(public_key) {
        var public_key_json = JSON.parse(public_key);
        return new paillierBigint.PublicKey(BigInt(public_key_json.n), BigInt(public_key_json.g));
    }

    async #load_homomorphic_private_key(private_key) {
        var private_key_json = JSON.parse(private_key);
        return new paillierBigint.PrivateKey(
            BigInt(private_key_json.lambda),
            BigInt(private_key_json.mu),
            new paillierBigint.PublicKey(BigInt(private_key_json.n), BigInt(private_key_json.g))
        );
    }

    /** Encrypt data with homomorphic encryption */
    async #encrypt_homomorphic(public_key, data) {
        return await public_key.encrypt(BigInt(data));
    }

    /** Add two bits of data under homomorphic encryption */
    async #add_homomorphic(public_key, ciphertext1, ciphertext2) {
        return await public_key.addition(ciphertext1, ciphertext2);
    }

    /** Decrypt data with homomorphic encryption */
    async #decrypt_homomorphic(private_key, ciphertext) {
        var tmp = await private_key.decrypt(BigInt(ciphertext.toString()));
        return tmp;
    }


    /** Generate a public private key for homomorphic encyrpted analytics. Only ever called on signup. Returns public key and encrypted form of private key. */
    async generate_analytics_keys() {
        var keypair = await this.#generate_homomorphic_keys();
        this.#AnalyticsEncryptionClientPublicKey = keypair.publicKey;
        this.#AnalyticsEncryptionClientPrivateKey = keypair.privateKey;

        var exported_public_key = JSON.stringify({n: this.#AnalyticsEncryptionClientPublicKey.n.toString(), g: this.#AnalyticsEncryptionClientPublicKey.g.toString()});
        var exported_private_key = JSON.stringify({lambda: this.#AnalyticsEncryptionClientPrivateKey.lambda.toString(), mu: this.#AnalyticsEncryptionClientPrivateKey.mu.toString(), n: this.#AnalyticsEncryptionClientPrivateKey.publicKey.n.toString(), g: this.#AnalyticsEncryptionClientPrivateKey.publicKey.g.toString()});

        var encrypted_private_key = await this.#encrypt_key_with_master_key(exported_private_key);

        return {
            "public_key" : exported_public_key,
            "encrypted_private_key" : encrypted_private_key
        };
    }

    /** Loads the public and private keys for homomorphic encrypted analytics */
    async load_analytics_keys(public_key, encrypted_private_key) {
        var private_key = await this.#decrypt_key_with_master_key(encrypted_private_key);

        var public_key_bytes = await this.#load_homomorphic_public_key(public_key);
        var private_key_bytes = await this.#load_homomorphic_private_key(private_key);

        this.#AnalyticsEncryptionClientPublicKey = public_key_bytes;
        this.#AnalyticsEncryptionClientPrivateKey = private_key_bytes;
    }

    /** Decrypt analytics with own private key */
    async decrypt_analytics(ciphertext) {
        return await this.#decrypt_homomorphic(this.#AnalyticsEncryptionClientPrivateKey, ciphertext);
    }

    /** Encrypt analytics with own public key */
    async #encrypt_analytics(plaintext) {
        return await this.#encrypt_homomorphic(this.#AnalyticsEncryptionClientPublicKey, plaintext);
    }

    /** Encrypt analytics with another public key */
    async #encrypt_analytics_with_key(public_key, plaintext) {

        public_key = await this.#load_homomorphic_public_key(public_key);

        return await this.#encrypt_homomorphic(public_key, plaintext);
    }

    /** Adds two values under homomorphic encryption using another user's public key */
    async #add_analytics_with_key(public_key, ciphertext1, ciphertext2) {

        public_key = await this.#load_homomorphic_public_key(public_key);

        return await this.#add_homomorphic(public_key, ciphertext1, ciphertext2);
    }

    /** Adds an intiger to a homomorphic ciphertext using another user's public key */
    async add_int_to_analytics_with_key(public_key, ciphertext, integer) {
        var ciphertext1 = BigInt(ciphertext);
        var ciphertext2 = await this.#encrypt_analytics_with_key(public_key, integer);

        var new_ciphertext = await this.#add_analytics_with_key(public_key, ciphertext1, ciphertext2);
        return new_ciphertext.toString();
    }

    /** Returns starting point for encrypted view duration */
    async get_encrypted_view_duration_start() {
        return (await this.#encrypt_analytics(0)).toString();
    }

    /** Returns starting point for encrypted reactions */
    async get_encrypted_reactions_start() {
        return (await this.#encrypt_analytics(0)).toString();
    }



  

}
