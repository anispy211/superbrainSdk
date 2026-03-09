"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Client = exports.SuperbrainError = void 0;
const koffi_1 = __importDefault(require("koffi"));
const os = __importStar(require("os"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
class SuperbrainError extends Error {
    constructor(message) {
        super(message);
        this.name = 'SuperbrainError';
    }
}
exports.SuperbrainError = SuperbrainError;
// Locate shared library
const libName = os.platform() === 'darwin' ? 'libsuperbrain.dylib' : 'libsuperbrain.so';
// Try finding it correctly in the package or local structure
let libPath = path.join(__dirname, '..', '..', 'lib', libName);
if (!fs.existsSync(libPath)) {
    libPath = path.join(process.cwd(), libName);
}
if (!fs.existsSync(libPath)) {
    libPath = path.join(process.cwd(), '..', 'lib', libName);
}
if (!fs.existsSync(libPath)) {
    throw new SuperbrainError(`Shared library ${libName} not found at ${libPath}. Ensure it is built and in the correct path.`);
}
const lib = koffi_1.default.load(libPath);
// C Bindings
const SB_NewClient = lib.func('SB_NewClient', 'str', ['str']);
const SB_NewClientWithEncryption = lib.func('SB_NewClientWithEncryption', 'str', ['str', 'uint8_t*', 'int']);
const SB_Register = lib.func('SB_Register', 'str', ['str', 'str']);
const SB_Allocate = lib.func('SB_Allocate', 'str', ['str', 'uint64_t']);
const SB_Write = lib.func('SB_Write', 'str', ['str', 'str', 'uint64_t', 'uint8_t*', 'uint64_t']);
const SB_Read = lib.func('SB_Read', 'str', ['str', 'str', 'uint64_t', 'uint64_t', '_Out_ uint8_t**', '_Out_ uint64_t*']);
const SB_Free = lib.func('SB_Free', 'str', ['str', 'str']);
class Client {
    clientId;
    constructor(addrs, encryptionKey) {
        let res;
        if (encryptionKey) {
            if (encryptionKey.length !== 32) {
                throw new SuperbrainError('Encryption key must be exactly 32 bytes for AES-GCM-256');
            }
            res = SB_NewClientWithEncryption(addrs, encryptionKey, encryptionKey.length);
        }
        else {
            res = SB_NewClient(addrs);
        }
        if (res && res.startsWith('error:')) {
            throw new SuperbrainError(res);
        }
        this.clientId = res;
    }
    register(agentId) {
        const res = SB_Register(this.clientId, agentId);
        if (res && res.startsWith('error:')) {
            throw new SuperbrainError(res);
        }
    }
    allocate(size) {
        const res = SB_Allocate(this.clientId, size);
        if (res && res.startsWith('error:')) {
            throw new SuperbrainError(res);
        }
        return res;
    }
    write(ptrId, offset, data) {
        const res = SB_Write(this.clientId, ptrId, offset, data, data.length);
        if (res && res.startsWith('error:')) {
            throw new SuperbrainError(res);
        }
    }
    read(ptrId, offset, length) {
        // Output pointers for koffi
        const outDataPtr = [null];
        const outLenPtr = [0];
        const res = SB_Read(this.clientId, ptrId, offset, length, outDataPtr, outLenPtr);
        if (res && res.startsWith('error:')) {
            throw new SuperbrainError(res);
        }
        const outBufPtr = outDataPtr[0];
        const outLen = outLenPtr[0];
        if (!outBufPtr || outLen === 0) {
            return Buffer.alloc(0);
        }
        // Decode the C string memory pointer into a Buffer
        const decodedBuffer = koffi_1.default.decode(outBufPtr, 'uint8_t', outLen);
        const buffer = Buffer.from(decodedBuffer);
        // Note: C-allocated pointer memory leak if we don't C-free, 
        // but for now Superbrain handles general lifecycle cleanup 
        // when client exists or pointer freed.
        return buffer;
    }
    free(ptrId) {
        const res = SB_Free(this.clientId, ptrId);
        if (res && res.startsWith('error:')) {
            throw new SuperbrainError(res);
        }
    }
}
exports.Client = Client;
