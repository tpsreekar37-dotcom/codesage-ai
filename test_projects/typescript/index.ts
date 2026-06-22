const secretKey = "sk_live_stripe_key_12345";
export function calculate(val: number): void {
    // nested loop
    for (let i = 0; i < 5; i++) {
        for (let j = 0; j < 5; j++) {
            console.log(i + j);
        }
    }
}