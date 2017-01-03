/*
Author: Arno0x0x, Twitter: @Arno0x0x
*/
using System;
using System.IO;
using System.Security.Cryptography;

namespace dropboxc2
{
    //****************************************************************************************
    // Class handling AES-128 CBC with PCKS7 padding cryptographic operations
    //****************************************************************************************
    static class Crypto
    {
        public static T[] SubArray<T>(this T[] data, int index, int length)
        {
            T[] result = new T[length];
            Array.Copy(data, index, result, 0, length);
            return result;
        }

        public static byte[] GetMD5Hash(byte[] source)
        {
            return new MD5CryptoServiceProvider().ComputeHash(source);
        }

        //--------------------------------------------------------------------------------------------------
        // Encrypts the given plaintext message byte array with a given 128 bits key
        // Returns the encrypted message as follow:
        // :==============:==================================================:
        // : IV(16bytes)  :   Encrypted(data + PKCS7 padding information)    :
        // :==============:==================================================:
        //--------------------------------------------------------------------------------------------------
        static public byte[] EncryptData(byte[] plainMessage, byte[] key)
        {
            #if (DEBUG)
                Console.WriteLine("\t\t[Crypto.EncryptData] Encrypting data...");
            #endif

            // Generate a random IV of 16 bytes
            RNGCryptoServiceProvider rngCsp = new RNGCryptoServiceProvider();
            byte[] IV = new byte[16];
            rngCsp.GetBytes(IV);
            //byte[] cipher = null;

            // Create an AesManaged object with the specified key and IV.
            using (AesManaged aes = new AesManaged())
            {
                aes.Padding = PaddingMode.PKCS7;
                aes.KeySize = 128;
                aes.Key = key;
                aes.IV = IV;

                using (MemoryStream ms = new MemoryStream())
                {
                    using (CryptoStream cs = new CryptoStream(ms, aes.CreateEncryptor(), CryptoStreamMode.Write))
                    {
                        cs.Write(IV, 0, 16);
                        cs.Write(plainMessage, 0, plainMessage.Length);
                    }

                    #if (DEBUG)
                        Console.WriteLine("\t\t[Crypto.EncryptData] Data encrypted");
                    #endif
                    return ms.ToArray();
                }
            }
        }

        //--------------------------------------------------------------------------------------------------
        // Decrypts the given a plaintext message byte array with a given 128 bits key
        // Returns the unencrypted message
        //--------------------------------------------------------------------------------------------------
        static public byte[] DecryptData(byte[] cipher, byte[] key)
        {
            #if (DEBUG)
                Console.WriteLine("\t\t[Crypto.DecryptData] Decrypting data...");
            #endif

            var IV = cipher.SubArray(0, 16);
            var encryptedMessage = cipher.SubArray(16, cipher.Length - 16);

            // Create an AesManaged object with the specified key and IV.
            using (AesManaged aes = new AesManaged())
            {
                aes.Padding = PaddingMode.PKCS7;
                aes.KeySize = 128;
                aes.Key = key;
                aes.IV = IV;

                using (MemoryStream ms = new MemoryStream())
                {
                    using (CryptoStream cs = new CryptoStream(ms, aes.CreateDecryptor(), CryptoStreamMode.Write))
                    {
                        cs.Write(encryptedMessage, 0, encryptedMessage.Length);
                    }

                    #if (DEBUG)
                          Console.WriteLine("\t\t[Crypto.DecryptData] Data decrypted");
                    #endif

                    return ms.ToArray();
                }
            }
        }
    }
}