import { Client, SuperbrainError } from './index';

async function main() {
    console.log("🤖 Node.js Superbrain Agent Demo");

    try {
        // We will assume the local cluster is running from earlier commands on port 50050
        const client = new Client('localhost:50050');
        console.log("✅ Custom Client initialized");

        client.register("typescript-demo-agent");
        console.log("✅ Agent registered to Secure Fabric");

        const dataStr = "Hello from Node.js (TypeScript) via Koffi/gRPC!";
        const dataBytes = Buffer.from(dataStr, 'utf-8');

        const ptr = client.allocate(dataBytes.length + 128);
        console.log(`✅ Allocated pointer: ${ptr}`);

        client.write(ptr, 0, dataBytes);
        console.log(`✅ Wrote data to pointer`);

        const readBuf = client.read(ptr, 0, dataBytes.length + 128);

        // Remove null padding
        const resultStr = readBuf.toString('utf-8').replace(/\0/g, '');
        console.log(`✅ Read verified: ${resultStr}`);

        client.free(ptr);
        console.log("🧹 Memory freed.");

    } catch (err: any) {
        console.error("Failed to run demo:", err.message);
    }
}

main();
