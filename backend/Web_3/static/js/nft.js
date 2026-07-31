/**
 * SCM platform - Web3 MetaMask Client Signature & Connection Engine
 * Location: static/js/nft.js
 */

window.walletSigner = function(challengeUrl, verifyUrl, csrfToken) {
    return {
        step: 1,
        walletAddress: '',
        errorMessage: '',
        isProcessing: false,
        
        async connectWallet() {
            if (!window.ethereum) {
                this.errorMessage = "MetaMask extension not detected. Please install MetaMask to initialize digital twins.";
                return;
            }
            try {
                this.isProcessing = true;
                const provider = new ethers.providers.Web3Provider(window.ethereum);
                await provider.send("eth_requestAccounts", []);
                const signer = provider.getSigner();
                this.walletAddress = await signer.getAddress();
                this.step = 2;
                this.errorMessage = '';
            } catch (err) {
                this.errorMessage = "Wallet connection rejected.";
            } finally {
                this.isProcessing = false;
            }
        },

        async signChallenge() {
            try {
                this.isProcessing = true;
                // 1. Fetch challenge nonce from Django
                const chalResponse = await fetch(challengeUrl);
                const chalData = await chalResponse.json();

                // 2. Request signature via MetaMask
                const provider = new ethers.providers.Web3Provider(window.ethereum);
                const signer = provider.getSigner();
                const signature = await signer.signMessage(chalData.challenge);

                // 3. Post verification payload to backend
                const formData = new FormData();
                formData.append('wallet_address', this.walletAddress);
                formData.append('signature', signature);
                formData.append('csrfmiddlewaretoken', csrfToken);

                const verifyResponse = await fetch(verifyUrl, {
                    method: 'POST',
                    body: formData
                });
                const verifyData = await verifyResponse.json();

                if (verifyData.success) {
                    this.step = 3;
                    this.errorMessage = '';
                } else {
                    this.errorMessage = verifyData.error || "Cryptographic verification failed.";
                }
            } catch (err) {
                this.errorMessage = "Challenge signing cancelled or failed.";
            } finally {
                this.isProcessing = false;
            }
        }
    }
}