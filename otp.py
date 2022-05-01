import hmac, hashlib, base64, datetime, time, unicodedata, math, random
from constants import *

# Way of string comoparison that can resist time-attacks
def string_equals(s1, s2):
    s1 = unicodedata.normalize('NFKC', s1)
    s2 = unicodedata.normalize('NFKC', s2)
    return hmac.compare_digest(s1.encode("utf-8"), s2.encode("utf-8"))


# Way of getting number of digits in a number that is much faster than len(str(num))
def digit_count(num):
    if num <= 999999999999997:
        return int(math.log10(num)) + 1
    else:
        counter = 15
        while num >= 10 ** counter:
            counter += 1
        return counter


# Way of getting nth digit of an integer that is much more efficient than str(num)[pos]
# Goes from right to left (123456 pos 0 = 6, 123456 pos 5 = 1)
def nth_digit(num, pos):
    return num // 10 ** pos % 10


class OTP:
    def __init__(self, s):
        self.secret = s
        self.digits = 6
        self.digest = hashlib.sha256
    
    def generate_otp(self, input: int):
        hasher = hmac.new(self.byte_secret(), self.int_to_bytestring(input), self.digest)
        hmac_hash = bytearray(hasher.digest())
        offset = hmac_hash[-1] & 0xf
        code = ((hmac_hash[offset] & 0x7f) << 24 |
                (hmac_hash[offset + 1] & 0xff) << 16 |
                (hmac_hash[offset + 2] & 0xff) << 8 |
                (hmac_hash[offset + 3] & 0xff))

        code = code % 10 ** (self.digits * 2)
        i = 0
        while digit_count(code) < self.digits * 2:
            code = code * 10 + nth_digit(input, i)
            i += 1
        
        alphanumeric_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        alphanumeric_code = ""
        for i in range(self.digits):
            alphanumeric_index = (nth_digit(code, i * 2) * nth_digit(code, i * 2 + 1)) % len(alphanumeric_chars)
            alphanumeric_code += alphanumeric_chars[alphanumeric_index]
        
        return alphanumeric_code

    def byte_secret(self):
        secret = self.secret
        missing_padding = len(secret) % 8
        if missing_padding != 0:
            secret += '=' * (8 - missing_padding)
        return base64.b32decode(secret, casefold=True)

    @staticmethod
    def int_to_bytestring(i, padding = 8):
        result = bytearray()
        while i != 0:
            result.append(i & 0xFF)
            i >>= 8

        return bytes(bytearray(reversed(result)).rjust(padding, b'\0'))
    
    @staticmethod
    def generate_secret():
        base32_characters = "234567ABCDEFGHIJKLMNOPQRSTUV"
        secret = ""
        for _ in range(SECRET_LENGTH):
            ch = random.choice(base32_characters)
            secret += ch
        
        return secret


class TOTP(OTP):
    def __init__(self, s, interval = EXPIRATION_TIME):
        super().__init__(s)
        self.interval = interval
    
    def verify(self, otp, valid_window = 5):
        curr_time = datetime.datetime.now()

        if valid_window:
            for i in range(-valid_window, valid_window + 1):
                if string_equals(str(otp), str(self.at(curr_time, i))):
                    return True
            return False

        return string_equals(str(otp), str(self.at(curr_time)))
    
    def at(self, for_time, counter_offset = 0):
        return self.generate_otp(self.timecode(for_time) + counter_offset)
    
    def now(self):
        return self.generate_otp(self.timecode(datetime.datetime.now()))
    
    def timecode(self, for_time: datetime.datetime):
        return int(time.mktime(for_time.timetuple()) / self.interval)