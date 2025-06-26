(function(b, a) {
    if (typeof define === "function" && define.amd) {
        define([], function() {
            (b.dcodeIO = b.dcodeIO || {})["Long"] = a()
        })
    } else {
        if (typeof require === "function" && typeof module === "object" && module && module.exports) {
            module.exports = a()
        } else {
            (b.dcodeIO = b.dcodeIO || {})["Long"] = a()
        }
    }
}
)(this, function() {
    function z(ai, ak, aj) {
        this.low = ai | 0;
        this.high = ak | 0;
        this.unsigned = !!aj
    }
    z.prototype.__isLong__;
    Object.defineProperty(z.prototype, "__isLong__", {
        value: true,
        enumerable: false,
        configurable: false
    });
    function f(ai) {
        return (ai && ai.__isLong__) === true
    }
    z.isLong = f;
    var V = {};
    var H = {};
    function ac(ak, aj) {
        var al, am, ai;
        if (aj) {
            ak >>>= 0;
            if (ai = (0 <= ak && ak < 256)) {
                am = H[ak];
                if (am) {
                    return am
                }
            }
            al = N(ak, (ak | 0) < 0 ? -1 : 0, true);
            if (ai) {
                H[ak] = al
            }
            return al
        } else {
            ak |= 0;
            if (ai = (-128 <= ak && ak < 128)) {
                am = V[ak];
                if (am) {
                    return am
                }
            }
            al = N(ak, ak < 0 ? -1 : 0, false);
            if (ai) {
                V[ak] = al
            }
            return al
        }
    }
    z.fromInt = ac;
    function l(aj, ai) {
        if (isNaN(aj) || !isFinite(aj)) {
            return ai ? h : A
        }
        if (ai) {
            if (aj < 0) {
                return h
            }
            if (aj >= c) {
                return y
            }
        } else {
            if (aj <= -x) {
                return O
            }
            if (aj + 1 >= x) {
                return a
            }
        }
        if (aj < 0) {
            return l(-aj, ai).neg()
        }
        return N((aj % d) | 0, (aj / d) | 0, ai)
    }
    z.fromNumber = l;
    function N(ai, ak, aj) {
        return new z(ai,ak,aj)
    }
    z.fromBits = N;
    var w = Math.pow;
    function G(am, ak, an) {
        if (am.length === 0) {
            throw Error("empty string")
        }
        if (am === "NaN" || am === "Infinity" || am === "+Infinity" || am === "-Infinity") {
            return A
        }
        if (typeof ak === "number") {
            an = ak,
            ak = false
        } else {
            ak = !!ak
        }
        an = an || 10;
        if (an < 2 || 36 < an) {
            throw RangeError("radix")
        }
        var aj;
        if ((aj = am.indexOf("-")) > 0) {
            throw Error("interior hyphen")
        } else {
            if (aj === 0) {
                return G(am.substring(1), ak, an).neg()
            }
        }
        var ap = l(w(an, 8));
        var ar = A;
        for (var al = 0; al < am.length; al += 8) {
            var aq = Math.min(8, am.length - al)
              , ao = parseInt(am.substring(al, al + aq), an);
            if (aq < 8) {
                var ai = l(w(an, aq));
                ar = ar.mul(ai).add(l(ao))
            } else {
                ar = ar.mul(ap);
                ar = ar.add(l(ao))
            }
        }
        ar.unsigned = ak;
        return ar
    }
    z.fromString = G;
    function F(ai) {
        if (ai instanceof z) {
            return ai
        }
        if (typeof ai === "number") {
            return l(ai)
        }
        if (typeof ai === "string") {
            return G(ai)
        }
        return N(ai.low, ai.high, ai.unsigned)
    }
    z.fromValue = F;
    var ad = 1 << 16;
    var ag = 1 << 24;
    var d = ad * ad;
    var c = d * d;
    var x = c / 2;
    var p = ac(ag);
    var A = ac(0);
    z.ZERO = A;
    var h = ac(0, true);
    z.UZERO = h;
    var R = ac(1);
    z.ONE = R;
    var J = ac(1, true);
    z.UONE = J;
    var b = ac(-1);
    z.NEG_ONE = b;
    var a = N(4294967295 | 0, 2147483647 | 0, false);
    z.MAX_VALUE = a;
    var y = N(4294967295 | 0, 4294967295 | 0, true);
    z.MAX_UNSIGNED_VALUE = y;
    var O = N(0, 2147483648 | 0, false);
    z.MIN_VALUE = O;
    var u = z.prototype;
    u.toInt = function q() {
        return this.unsigned ? this.low >>> 0 : this.low
    }
    ;
    u.toNumber = function Z() {
        if (this.unsigned) {
            return ((this.high >>> 0) * d) + (this.low >>> 0)
        }
        return this.high * d + (this.low >>> 0)
    }
    ;
    u.toString = function i(an) {
        an = an || 10;
        if (an < 2 || 36 < an) {
            throw RangeError("radix")
        }
        if (this.isZero()) {
            return "0"
        }
        if (this.isNegative()) {
            if (this.eq(O)) {
                var al = l(an)
                  , ai = this.div(al)
                  , ak = ai.mul(al).sub(this);
                return ai.toString(an) + ak.toInt().toString(an)
            } else {
                return "-" + this.neg().toString(an)
            }
        }
        var aq = l(w(an, 6), this.unsigned)
          , ap = this;
        var ar = "";
        while (true) {
            var ao = ap.div(aq)
              , am = ap.sub(ao.mul(aq)).toInt() >>> 0
              , aj = am.toString(an);
            ap = ao;
            if (ap.isZero()) {
                return aj + ar
            } else {
                while (aj.length < 6) {
                    aj = "0" + aj
                }
                ar = "" + aj + ar
            }
        }
    }
    ;
    u.getHighBits = function aa() {
        return this.high
    }
    ;
    u.getHighBitsUnsigned = function k() {
        return this.high >>> 0
    }
    ;
    u.getLowBits = function t() {
        return this.low
    }
    ;
    u.getLowBitsUnsigned = function P() {
        return this.low >>> 0
    }
    ;
    u.getNumBitsAbs = function ae() {
        if (this.isNegative()) {
            return this.eq(O) ? 64 : this.neg().getNumBitsAbs()
        }
        var aj = this.high != 0 ? this.high : this.low;
        for (var ai = 31; ai > 0; ai--) {
            if ((aj & (1 << ai)) != 0) {
                break
            }
        }
        return this.high != 0 ? ai + 33 : ai + 1
    }
    ;
    u.isZero = function M() {
        return this.high === 0 && this.low === 0
    }
    ;
    u.isNegative = function S() {
        return !this.unsigned && this.high < 0
    }
    ;
    u.isPositive = function Y() {
        return this.unsigned || this.high >= 0
    }
    ;
    u.isOdd = function Q() {
        return (this.low & 1) === 1
    }
    ;
    u.isEven = function s() {
        return (this.low & 1) === 0
    }
    ;
    u.equals = function I(ai) {
        if (!f(ai)) {
            ai = F(ai)
        }
        if (this.unsigned !== ai.unsigned && (this.high >>> 31) === 1 && (ai.high >>> 31) === 1) {
            return false
        }
        return this.high === ai.high && this.low === ai.low
    }
    ;
    u.eq = u.equals;
    u.notEquals = function ab(ai) {
        return !this.eq(ai)
    }
    ;
    u.neq = u.notEquals;
    u.lessThan = function o(ai) {
        return this.comp(ai) < 0
    }
    ;
    u.lt = u.lessThan;
    u.lessThanOrEqual = function U(ai) {
        return this.comp(ai) <= 0
    }
    ;
    u.lte = u.lessThanOrEqual;
    u.greaterThan = function j(ai) {
        return this.comp(ai) > 0
    }
    ;
    u.gt = u.greaterThan;
    u.greaterThanOrEqual = function L(ai) {
        return this.comp(ai) >= 0
    }
    ;
    u.gte = u.greaterThanOrEqual;
    u.compare = function n(aj) {
        if (!f(aj)) {
            aj = F(aj)
        }
        if (this.eq(aj)) {
            return 0
        }
        var ai = this.isNegative()
          , ak = aj.isNegative();
        if (ai && !ak) {
            return -1
        }
        if (!ai && ak) {
            return 1
        }
        if (!this.unsigned) {
            return this.sub(aj).isNegative() ? -1 : 1
        }
        return (aj.high >>> 0) > (this.high >>> 0) || (aj.high === this.high && (aj.low >>> 0) > (this.low >>> 0)) ? -1 : 1
    }
    ;
    u.comp = u.compare;
    u.negate = function r() {
        if (!this.unsigned && this.eq(O)) {
            return O
        }
        return this.not().add(R)
    }
    ;
    u.neg = u.negate;
    u.add = function e(al) {
        if (!f(al)) {
            al = F(al)
        }
        var ao = this.high >>> 16;
        var aj = this.high & 65535;
        var aq = this.low >>> 16;
        var ak = this.low & 65535;
        var at = al.high >>> 16;
        var am = al.high & 65535;
        var au = al.low >>> 16;
        var an = al.low & 65535;
        var av = 0
          , ap = 0
          , ai = 0
          , ar = 0;
        ar += ak + an;
        ai += ar >>> 16;
        ar &= 65535;
        ai += aq + au;
        ap += ai >>> 16;
        ai &= 65535;
        ap += aj + am;
        av += ap >>> 16;
        ap &= 65535;
        av += ao + at;
        av &= 65535;
        return N((ai << 16) | ar, (av << 16) | ap, this.unsigned)
    }
    ;
    u.subtract = function m(ai) {
        if (!f(ai)) {
            ai = F(ai)
        }
        return this.add(ai.neg())
    }
    ;
    u.sub = u.subtract;
    u.multiply = function D(au) {
        if (this.isZero()) {
            return A
        }
        if (!f(au)) {
            au = F(au)
        }
        if (au.isZero()) {
            return A
        }
        if (this.eq(O)) {
            return au.isOdd() ? O : A
        }
        if (au.eq(O)) {
            return this.isOdd() ? O : A
        }
        if (this.isNegative()) {
            if (au.isNegative()) {
                return this.neg().mul(au.neg())
            } else {
                return this.neg().mul(au).neg()
            }
        } else {
            if (au.isNegative()) {
                return this.mul(au.neg()).neg()
            }
        }
        if (this.lt(p) && au.lt(p)) {
            return l(this.toNumber() * au.toNumber(), this.unsigned)
        }
        var an = this.high >>> 16;
        var aj = this.high & 65535;
        var ap = this.low >>> 16;
        var ak = this.low & 65535;
        var ar = au.high >>> 16;
        var al = au.high & 65535;
        var at = au.low >>> 16;
        var am = au.low & 65535;
        var av = 0
          , ao = 0
          , ai = 0
          , aq = 0;
        aq += ak * am;
        ai += aq >>> 16;
        aq &= 65535;
        ai += ap * am;
        ao += ai >>> 16;
        ai &= 65535;
        ai += ak * at;
        ao += ai >>> 16;
        ai &= 65535;
        ao += aj * am;
        av += ao >>> 16;
        ao &= 65535;
        ao += ap * at;
        av += ao >>> 16;
        ao &= 65535;
        ao += ak * al;
        av += ao >>> 16;
        ao &= 65535;
        av += an * am + aj * at + ap * al + ak * ar;
        av &= 65535;
        return N((ai << 16) | aq, (av << 16) | ao, this.unsigned)
    }
    ;
    u.mul = u.multiply;
    u.divide = function E(ai) {
        if (!f(ai)) {
            ai = F(ai)
        }
        if (ai.isZero()) {
            throw Error("division by zero")
        }
        if (this.isZero()) {
            return this.unsigned ? h : A
        }
        var an, ap, al;
        if (!this.unsigned) {
            if (this.eq(O)) {
                if (ai.eq(R) || ai.eq(b)) {
                    return O
                } else {
                    if (ai.eq(O)) {
                        return R
                    } else {
                        var aj = this.shr(1);
                        an = aj.div(ai).shl(1);
                        if (an.eq(A)) {
                            return ai.isNegative() ? R : b
                        } else {
                            ap = this.sub(ai.mul(an));
                            al = an.add(ap.div(ai));
                            return al
                        }
                    }
                }
            } else {
                if (ai.eq(O)) {
                    return this.unsigned ? h : A
                }
            }
            if (this.isNegative()) {
                if (ai.isNegative()) {
                    return this.neg().div(ai.neg())
                }
                return this.neg().div(ai).neg()
            } else {
                if (ai.isNegative()) {
                    return this.div(ai.neg()).neg()
                }
            }
            al = A
        } else {
            if (!ai.unsigned) {
                ai = ai.toUnsigned()
            }
            if (ai.gt(this)) {
                return h
            }
            if (ai.gt(this.shru(1))) {
                return J
            }
            al = h
        }
        ap = this;
        while (ap.gte(ai)) {
            an = Math.max(1, Math.floor(ap.toNumber() / ai.toNumber()));
            var aq = Math.ceil(Math.log(an) / Math.LN2)
              , ao = (aq <= 48) ? 1 : w(2, aq - 48)
              , ak = l(an)
              , am = ak.mul(ai);
            while (am.isNegative() || am.gt(ap)) {
                an -= ao;
                ak = l(an, this.unsigned);
                am = ak.mul(ai)
            }
            if (ak.isZero()) {
                ak = R
            }
            al = al.add(ak);
            ap = ap.sub(am)
        }
        return al
    }
    ;
    u.div = u.divide;
    u.modulo = function af(ai) {
        if (!f(ai)) {
            ai = F(ai)
        }
        return this.sub(this.div(ai).mul(ai))
    }
    ;
    u.mod = u.modulo;
    u.not = function X() {
        return N(~this.low, ~this.high, this.unsigned)
    }
    ;
    u.and = function W(ai) {
        if (!f(ai)) {
            ai = F(ai)
        }
        return N(this.low & ai.low, this.high & ai.high, this.unsigned)
    }
    ;
    u.or = function K(ai) {
        if (!f(ai)) {
            ai = F(ai)
        }
        return N(this.low | ai.low, this.high | ai.high, this.unsigned)
    }
    ;
    u.xor = function T(ai) {
        if (!f(ai)) {
            ai = F(ai)
        }
        return N(this.low ^ ai.low, this.high ^ ai.high, this.unsigned)
    }
    ;
    u.shiftLeft = function v(ai) {
        if (f(ai)) {
            ai = ai.toInt()
        }
        if ((ai &= 63) === 0) {
            return this
        } else {
            if (ai < 32) {
                return N(this.low << ai, (this.high << ai) | (this.low >>> (32 - ai)), this.unsigned)
            } else {
                return N(0, this.low << (ai - 32), this.unsigned)
            }
        }
    }
    ;
    u.shl = u.shiftLeft;
    u.shiftRight = function g(ai) {
        if (f(ai)) {
            ai = ai.toInt()
        }
        if ((ai &= 63) === 0) {
            return this
        } else {
            if (ai < 32) {
                return N((this.low >>> ai) | (this.high << (32 - ai)), this.high >> ai, this.unsigned)
            } else {
                return N(this.high >> (ai - 32), this.high >= 0 ? 0 : -1, this.unsigned)
            }
        }
    }
    ;
    u.shr = u.shiftRight;
    u.shiftRightUnsigned = function B(ak) {
        if (f(ak)) {
            ak = ak.toInt()
        }
        ak &= 63;
        if (ak === 0) {
            return this
        } else {
            var aj = this.high;
            if (ak < 32) {
                var ai = this.low;
                return N((ai >>> ak) | (aj << (32 - ak)), aj >>> ak, this.unsigned)
            } else {
                if (ak === 32) {
                    return N(aj, 0, this.unsigned)
                } else {
                    return N(aj >>> (ak - 32), 0, this.unsigned)
                }
            }
        }
    }
    ;
    u.shru = u.shiftRightUnsigned;
    u.toSigned = function ah() {
        if (!this.unsigned) {
            return this
        }
        return N(this.low, this.high, false)
    }
    ;
    u.toUnsigned = function C() {
        if (this.unsigned) {
            return this
        }
        return N(this.low, this.high, true)
    }
    ;
    u.toBytes = function(ai) {
        return ai ? this.toBytesLE() : this.toBytesBE()
    }
    ;
    u.toBytesLE = function() {
        var ai = this.high
          , aj = this.low;
        return [aj & 255, (aj >>> 8) & 255, (aj >>> 16) & 255, (aj >>> 24) & 255, ai & 255, (ai >>> 8) & 255, (ai >>> 16) & 255, (ai >>> 24) & 255]
    }
    ;
    u.toBytesBE = function() {
        var ai = this.high
          , aj = this.low;
        return [(ai >>> 24) & 255, (ai >>> 16) & 255, (ai >>> 8) & 255, ai & 255, (aj >>> 24) & 255, (aj >>> 16) & 255, (aj >>> 8) & 255, aj & 255]
    }
    ;
    return z
});
if (typeof Paho === "undefined") {
    Paho = {}
}
Paho.MQTT = (function(r) {
    var h = "@VERSION@";
    var k = "@BUILDLEVEL@";
    var o = {
        CONNECT: 1,
        CONNACK: 2,
        PUBLISH: 3,
        PUBACK: 4,
        PUBREC: 5,
        PUBREL: 6,
        PUBCOMP: 7,
        SUBSCRIBE: 8,
        SUBACK: 9,
        UNSUBSCRIBE: 10,
        UNSUBACK: 11,
        PINGREQ: 12,
        PINGRESP: 13,
        DISCONNECT: 14
    };
    var m = function(C, B) {
        for (var z in C) {
            if (C.hasOwnProperty(z)) {
                if (B.hasOwnProperty(z)) {
                    if (typeof C[z] !== B[z]) {
                        throw new Error(u(j.INVALID_TYPE, [typeof C[z], z]))
                    }
                } else {
                    var A = "Unknown property, " + z + ". Valid properties are:";
                    for (var z in B) {
                        if (B.hasOwnProperty(z)) {
                            A = A + " " + z
                        }
                    }
                    throw new Error(A)
                }
            }
        }
    };
    var b = function(A, z) {
        return function() {
            return A.apply(z, arguments)
        }
    };
    var j = {
        OK: {
            code: 0,
            text: "AMQJSC0000I OK."
        },
        CONNECT_TIMEOUT: {
            code: 1,
            text: "AMQJSC0001E Connect timed out."
        },
        SUBSCRIBE_TIMEOUT: {
            code: 2,
            text: "AMQJS0002E Subscribe timed out."
        },
        UNSUBSCRIBE_TIMEOUT: {
            code: 3,
            text: "AMQJS0003E Unsubscribe timed out."
        },
        PING_TIMEOUT: {
            code: 4,
            text: "AMQJS0004E Ping timed out."
        },
        INTERNAL_ERROR: {
            code: 5,
            text: "AMQJS0005E Internal error. Error Message: {0}, Stack trace: {1}"
        },
        CONNACK_RETURNCODE: {
            code: 6,
            text: "AMQJS0006E Bad Connack return code:{0} {1}."
        },
        SOCKET_ERROR: {
            code: 7,
            text: "AMQJS0007E Socket error:{0}."
        },
        SOCKET_CLOSE: {
            code: 8,
            text: "AMQJS0008I Socket closed."
        },
        MALFORMED_UTF: {
            code: 9,
            text: "AMQJS0009E Malformed UTF data:{0} {1} {2}."
        },
        UNSUPPORTED: {
            code: 10,
            text: "AMQJS0010E {0} is not supported by this browser."
        },
        INVALID_STATE: {
            code: 11,
            text: "AMQJS0011E Invalid state {0}."
        },
        INVALID_TYPE: {
            code: 12,
            text: "AMQJS0012E Invalid type {0} for {1}."
        },
        INVALID_ARGUMENT: {
            code: 13,
            text: "AMQJS0013E Invalid argument {0} for {1}."
        },
        UNSUPPORTED_OPERATION: {
            code: 14,
            text: "AMQJS0014E Unsupported operation."
        },
        INVALID_STORED_DATA: {
            code: 15,
            text: "AMQJS0015E Invalid data in local storage key={0} value={1}."
        },
        INVALID_MQTT_MESSAGE_TYPE: {
            code: 16,
            text: "AMQJS0016E Invalid MQTT message type {0}."
        },
        MALFORMED_UNICODE: {
            code: 17,
            text: "AMQJS0017E Malformed Unicode string:{0} {1}."
        }
    };
    var f = {
        0: "Connection Accepted",
        1: "Connection Refused: unacceptable protocol version",
        2: "Connection Refused: identifier rejected",
        3: "Connection Refused: server unavailable",
        4: "Connection Refused: bad user name or password",
        5: "Connection Refused: not authorized"
    };
    var u = function(z, B) {
        var F = z.text;
        if (B) {
            var E, G;
            for (var A = 0; A < B.length; A++) {
                E = "{" + A + "}";
                G = F.indexOf(E);
                if (G > 0) {
                    var D = F.substring(0, G);
                    var C = F.substring(G + E.length);
                    F = D + B[A] + C
                }
            }
        }
        return F
    };
    var e = [0, 6, 77, 81, 73, 115, 100, 112, 3];
    var d = [0, 4, 77, 81, 84, 84, 4];
    var q = function(B, A) {
        this.type = B;
        for (var z in A) {
            if (A.hasOwnProperty(z)) {
                this[z] = A[z]
            }
        }
    };
    q.prototype.encode = function() {
        var H = ((this.type & 15) << 4);
        var K = 0;
        var A = new Array();
        var D = 0;
        if (this.messageIdentifier != undefined) {
            K += 2
        }
        switch (this.type) {
        case o.CONNECT:
            switch (this.mqttVersion) {
            case 3:
                K += e.length + 3;
                break;
            case 4:
                K += d.length + 3;
                break
            }
            K += c(this.clientId) + 2;
            if (this.willMessage != undefined) {
                K += c(this.willMessage.destinationName) + 2;
                var C = this.willMessage.payloadBytes;
                if (!(C instanceof Uint8Array)) {
                    C = new Uint8Array(F)
                }
                K += C.byteLength + 2
            }
            if (this.userName != undefined) {
                K += c(this.userName) + 2
            }
            if (this.password != undefined) {
                K += c(this.password) + 2
            }
            break;
        case o.SUBSCRIBE:
            H |= 2;
            for (var G = 0; G < this.topics.length; G++) {
                A[G] = c(this.topics[G]);
                K += A[G] + 2
            }
            K += this.requestedQos.length;
            break;
        case o.UNSUBSCRIBE:
            H |= 2;
            for (var G = 0; G < this.topics.length; G++) {
                A[G] = c(this.topics[G]);
                K += A[G] + 2
            }
            break;
        case o.PUBREL:
            H |= 2;
            break;
        case o.PUBLISH:
            if (this.payloadMessage.duplicate) {
                H |= 8
            }
            H = H |= (this.payloadMessage.qos << 1);
            if (this.payloadMessage.retained) {
                H |= 1
            }
            D = c(this.payloadMessage.destinationName);
            K += D + 2;
            var F = this.payloadMessage.payloadBytes;
            K += F.byteLength;
            if (F instanceof ArrayBuffer) {
                F = new Uint8Array(F)
            } else {
                if (!(F instanceof Uint8Array)) {
                    F = new Uint8Array(F.buffer)
                }
            }
            break;
        case o.DISCONNECT:
            break;
        default:
        }
        var z = x(K);
        var J = z.length + 1;
        var B = new ArrayBuffer(K + J);
        var I = new Uint8Array(B);
        I[0] = H;
        I.set(z, 1);
        if (this.type == o.PUBLISH) {
            J = t(this.payloadMessage.destinationName, D, I, J)
        } else {
            if (this.type == o.CONNECT) {
                switch (this.mqttVersion) {
                case 3:
                    I.set(e, J);
                    J += e.length;
                    break;
                case 4:
                    I.set(d, J);
                    J += d.length;
                    break
                }
                var E = 0;
                if (this.cleanSession) {
                    E = 2
                }
                if (this.willMessage != undefined) {
                    E |= 4;
                    E |= (this.willMessage.qos << 3);
                    if (this.willMessage.retained) {
                        E |= 32
                    }
                }
                if (this.userName != undefined) {
                    E |= 128
                }
                if (this.password != undefined) {
                    E |= 64
                }
                I[J++] = E;
                J = y(this.keepAliveInterval, I, J)
            }
        }
        if (this.messageIdentifier != undefined) {
            J = y(this.messageIdentifier, I, J)
        }
        switch (this.type) {
        case o.CONNECT:
            J = t(this.clientId, c(this.clientId), I, J);
            if (this.willMessage != undefined) {
                J = t(this.willMessage.destinationName, c(this.willMessage.destinationName), I, J);
                J = y(C.byteLength, I, J);
                I.set(C, J);
                J += C.byteLength
            }
            if (this.userName != undefined) {
                J = t(this.userName, c(this.userName), I, J)
            }
            if (this.password != undefined) {
                J = t(this.password, c(this.password), I, J)
            }
            break;
        case o.PUBLISH:
            I.set(F, J);
            break;
        case o.SUBSCRIBE:
            for (var G = 0; G < this.topics.length; G++) {
                J = t(this.topics[G], A[G], I, J);
                I[J++] = this.requestedQos[G]
            }
            break;
        case o.UNSUBSCRIBE:
            for (var G = 0; G < this.topics.length; G++) {
                J = t(this.topics[G], A[G], I, J)
            }
            break;
        default:
        }
        return B
    }
    ;
    function g(K, H) {
        var F = H;
        var D = K[H];
        var G = D >> 4;
        var z = D &= 15;
        H += 1;
        var I;
        var J = 0;
        var N = 1;
        do {
            if (H == K.length) {
                return [null, F]
            }
            I = K[H++];
            J += ((I & 127) * N);
            N *= 128
        } while ((I & 128) != 0);
        var B = H + J;
        if (B > K.length) {
            return [null, F]
        }
        var L = new q(G);
        switch (G) {
        case o.CONNACK:
            var C = K[H++];
            if (C & 1) {
                L.sessionPresent = true
            }
            L.returnCode = K[H++];
            break;
        case o.PUBLISH:
            var M = (z >> 1) & 3;
            var E = l(K, H);
            H += 2;
            var A = n(K, H, E);
            H += E;
            if (M > 0) {
                L.messageIdentifier = l(K, H);
                H += 2
            }
            var O = new Paho.MQTT.Message(K.subarray(H, B));
            if ((z & 1) == 1) {
                O.retained = true
            }
            if ((z & 8) == 8) {
                O.duplicate = true
            }
            O.qos = M;
            O.destinationName = A;
            L.payloadMessage = O;
            break;
        case o.PUBACK:
        case o.PUBREC:
        case o.PUBREL:
        case o.PUBCOMP:
        case o.UNSUBACK:
            L.messageIdentifier = l(K, H);
            break;
        case o.SUBACK:
            L.messageIdentifier = l(K, H);
            H += 2;
            L.returnCode = K.subarray(H, B);
            break;
        default:
        }
        return [L, B]
    }
    function y(A, z, B) {
        z[B++] = A >> 8;
        z[B++] = A % 256;
        return B
    }
    function t(A, B, z, C) {
        C = y(B, z, C);
        i(A, z, C);
        return C + B
    }
    function l(z, A) {
        return 256 * z[A] + z[A + 1]
    }
    function x(B) {
        var z = new Array(1);
        var A = 0;
        do {
            var C = B % 128;
            B = B >> 7;
            if (B > 0) {
                C |= 128
            }
            z[A++] = C
        } while ((B > 0) && (A < 4));
        return z
    }
    function c(B) {
        var A = 0;
        for (var C = 0; C < B.length; C++) {
            var z = B.charCodeAt(C);
            if (z > 2047) {
                if (55296 <= z && z <= 56319) {
                    C++;
                    A++
                }
                A += 3
            } else {
                if (z > 127) {
                    A += 2
                } else {
                    A++
                }
            }
        }
        return A
    }
    function i(B, A, F) {
        var E = F;
        for (var C = 0; C < B.length; C++) {
            var z = B.charCodeAt(C);
            if (55296 <= z && z <= 56319) {
                var D = B.charCodeAt(++C);
                if (isNaN(D)) {
                    throw new Error(u(j.MALFORMED_UNICODE, [z, D]))
                }
                z = ((z - 55296) << 10) + (D - 56320) + 65536
            }
            if (z <= 127) {
                A[E++] = z
            } else {
                if (z <= 2047) {
                    A[E++] = z >> 6 & 31 | 192;
                    A[E++] = z & 63 | 128
                } else {
                    if (z <= 65535) {
                        A[E++] = z >> 12 & 15 | 224;
                        A[E++] = z >> 6 & 63 | 128;
                        A[E++] = z & 63 | 128
                    } else {
                        A[E++] = z >> 18 & 7 | 240;
                        A[E++] = z >> 12 & 63 | 128;
                        A[E++] = z >> 6 & 63 | 128;
                        A[E++] = z & 63 | 128
                    }
                }
            }
        }
        return A
    }
    function n(G, C, z) {
        var A = "";
        var B;
        var E = C;
        while (E < C + z) {
            var I = G[E++];
            if (I < 128) {
                B = I
            } else {
                var H = G[E++] - 128;
                if (H < 0) {
                    throw new Error(u(j.MALFORMED_UTF, [I.toString(16), H.toString(16), ""]))
                }
                if (I < 224) {
                    B = 64 * (I - 192) + H
                } else {
                    var F = G[E++] - 128;
                    if (F < 0) {
                        throw new Error(u(j.MALFORMED_UTF, [I.toString(16), H.toString(16), F.toString(16)]))
                    }
                    if (I < 240) {
                        B = 4096 * (I - 224) + 64 * H + F
                    } else {
                        var D = G[E++] - 128;
                        if (D < 0) {
                            throw new Error(u(j.MALFORMED_UTF, [I.toString(16), H.toString(16), F.toString(16), D.toString(16)]))
                        }
                        if (I < 248) {
                            B = 262144 * (I - 240) + 4096 * H + 64 * F + D
                        } else {
                            throw new Error(u(j.MALFORMED_UTF, [I.toString(16), H.toString(16), F.toString(16), D.toString(16)]))
                        }
                    }
                }
            }
            if (B > 65535) {
                B -= 65536;
                A += String.fromCharCode(55296 + (B >> 10));
                B = 56320 + (B & 1023)
            }
            A += String.fromCharCode(B)
        }
        return A
    }
    var s = function(z, E, D) {
        this._client = z;
        this._window = E;
        this._keepAliveInterval = D * 1000;
        this.isReset = false;
        var C = new q(o.PINGREQ).encode();
        var B = function(F) {
            return function() {
                return A.apply(F)
            }
        };
        var A = function() {
            if (!this.isReset) {
                this._client._trace("Pinger.doPing", "Timed out");
                this._client._disconnected(j.PING_TIMEOUT.code, u(j.PING_TIMEOUT))
            } else {
                this.isReset = false;
                this._client._trace("Pinger.doPing", "send PINGREQ");
                this._client.socket.send(C);
                this.timeout = this._window.setTimeout(B(this), this._keepAliveInterval)
            }
        };
        this.reset = function() {
            this.isReset = true;
            this._window.clearTimeout(this.timeout);
            if (this._keepAliveInterval > 0) {
                this.timeout = setTimeout(B(this), this._keepAliveInterval)
            }
        }
        ;
        this.cancel = function() {
            this._window.clearTimeout(this.timeout)
        }
    };
    var w = function(z, D, B, E, A) {
        this._window = D;
        if (!B) {
            B = 30
        }
        var C = function(H, F, G) {
            return function() {
                return H.apply(F, G)
            }
        };
        this.timeout = setTimeout(C(E, z, A), B * 1000);
        this.cancel = function() {
            this._window.clearTimeout(this.timeout)
        }
    };
    var v = function(D, C, A, E, z) {
        if (!("WebSocket"in r && r.WebSocket !== null)) {
            throw new Error(u(j.UNSUPPORTED, ["WebSocket"]))
        }
        if (!("localStorage"in r && r.localStorage !== null)) {
            throw new Error(u(j.UNSUPPORTED, ["localStorage"]))
        }
        if (!("ArrayBuffer"in r && r.ArrayBuffer !== null)) {
            throw new Error(u(j.UNSUPPORTED, ["ArrayBuffer"]))
        }
        this._trace("Paho.MQTT.Client", D, C, A, E, z);
        this.host = C;
        this.port = A;
        this.path = E;
        this.uri = D;
        this.clientId = z;
        this._localKey = C + ":" + A + (E != "/mqtt" ? ":" + E : "") + ":" + z + ":";
        this._msg_queue = [];
        this._sentMessages = {};
        this._receivedMessages = {};
        this._notify_msg_sent = {};
        this._message_identifier = 1;
        this._sequence = 0;
        for (var B in localStorage) {
            if (B.indexOf("Sent:" + this._localKey) == 0 || B.indexOf("Received:" + this._localKey) == 0) {
                this.restore(B)
            }
        }
    };
    v.prototype.host;
    v.prototype.port;
    v.prototype.path;
    v.prototype.uri;
    v.prototype.clientId;
    v.prototype.socket;
    v.prototype.connected = false;
    v.prototype.maxMessageIdentifier = 65536;
    v.prototype.connectOptions;
    v.prototype.hostIndex;
    v.prototype.onConnectionLost;
    v.prototype.onMessageDelivered;
    v.prototype.onMessageArrived;
    v.prototype.traceFunction;
    v.prototype._msg_queue = null;
    v.prototype._connectTimeout;
    v.prototype.sendPinger = null;
    v.prototype.receivePinger = null;
    v.prototype.receiveBuffer = null;
    v.prototype._traceBuffer = null;
    v.prototype._MAX_TRACE_ENTRIES = 100;
    v.prototype.connect = function(A) {
        var z = this._traceMask(A, "password");
        this._trace("Client.connect", z, this.socket, this.connected);
        this.connectOptions = A;
        if (A.uris) {
            this.hostIndex = 0;
            this._doConnect(A.uris[0])
        } else {
            this._doConnect(this.uri)
        }
    }
    ;
    v.prototype.subscribe = function(A, z) {
        this._trace("Client.subscribe", A, z);
        if (!this.connected) {
            throw new Error(u(j.INVALID_STATE, ["not connected"]))
        }
        var B = new q(o.SUBSCRIBE);
        B.topics = [A];
        if (z.qos != undefined) {
            B.requestedQos = [z.qos]
        } else {
            B.requestedQos = [0]
        }
        if (z.onSuccess) {
            B.onSuccess = function(C) {
                z.onSuccess({
                    invocationContext: z.invocationContext,
                    grantedQos: C
                })
            }
        }
        if (z.onFailure) {
            B.onFailure = function(C) {
                z.onFailure({
                    invocationContext: z.invocationContext,
                    errorCode: C
                })
            }
        }
        if (z.timeout) {
            B.timeOut = new w(this,window,z.timeout,z.onFailure,[{
                invocationContext: z.invocationContext,
                errorCode: j.SUBSCRIBE_TIMEOUT.code,
                errorMessage: u(j.SUBSCRIBE_TIMEOUT)
            }])
        }
        this._requires_ack(B);
        this._schedule_message(B)
    }
    ;
    v.prototype.unsubscribe = function(A, z) {
        this._trace("Client.unsubscribe", A, z);
        if (!this.connected) {
            throw new Error(u(j.INVALID_STATE, ["not connected"]))
        }
        var B = new q(o.UNSUBSCRIBE);
        B.topics = [A];
        if (z.onSuccess) {
            B.callback = function() {
                z.onSuccess({
                    invocationContext: z.invocationContext
                })
            }
        }
        if (z.timeout) {
            B.timeOut = new w(this,window,z.timeout,z.onFailure,[{
                invocationContext: z.invocationContext,
                errorCode: j.UNSUBSCRIBE_TIMEOUT.code,
                errorMessage: u(j.UNSUBSCRIBE_TIMEOUT)
            }])
        }
        this._requires_ack(B);
        this._schedule_message(B)
    }
    ;
    v.prototype.send = function(z) {
        this._trace("Client.send", z);
        if (!this.connected) {
            throw new Error(u(j.INVALID_STATE, ["not connected"]))
        }
        wireMessage = new q(o.PUBLISH);
        wireMessage.payloadMessage = z;
        if (z.qos > 0) {
            this._requires_ack(wireMessage)
        } else {
            if (this.onMessageDelivered) {
                this._notify_msg_sent[wireMessage] = this.onMessageDelivered(wireMessage.payloadMessage)
            }
        }
        this._schedule_message(wireMessage)
    }
    ;
    v.prototype.disconnect = function() {
        this._trace("Client.disconnect");
        if (!this.socket) {
            throw new Error(u(j.INVALID_STATE, ["not connecting or connected"]))
        }
        wireMessage = new q(o.DISCONNECT);
        this._notify_msg_sent[wireMessage] = b(this._disconnected, this);
        this._schedule_message(wireMessage)
    }
    ;
    v.prototype.getTraceLog = function() {
        if (this._traceBuffer !== null) {
            this._trace("Client.getTraceLog", new Date());
            this._trace("Client.getTraceLog in flight messages", this._sentMessages.length);
            for (var z in this._sentMessages) {
                this._trace("_sentMessages ", z, this._sentMessages[z])
            }
            for (var z in this._receivedMessages) {
                this._trace("_receivedMessages ", z, this._receivedMessages[z])
            }
            return this._traceBuffer
        }
    }
    ;
    v.prototype.startTrace = function() {
        if (this._traceBuffer === null) {
            this._traceBuffer = []
        }
        this._trace("Client.startTrace", new Date(), h)
    }
    ;
    v.prototype.stopTrace = function() {
        delete this._traceBuffer
    }
    ;
    v.prototype._doConnect = function(A) {
        if (this.connectOptions.useSSL) {
            var z = A.split(":");
            z[0] = "wss";
            A = z.join(":")
        }
        this.connected = false;
        if (this.connectOptions.token) {
            if (this.connectOptions.mqttVersion < 4) {
                this.socket = new WebSocket(A,[this.connectOptions.token])
            } else {
                this.socket = new WebSocket(A,[this.connectOptions.token])
            }
        } else {
            if (this.connectOptions.mqttVersion < 4) {
                this.socket = new WebSocket(A)
            } else {
                this.socket = new WebSocket(A)
            }
        }
        this.socket.binaryType = "arraybuffer";
        this.socket.onopen = b(this._on_socket_open, this);
        this.socket.onmessage = b(this._on_socket_message, this);
        this.socket.onerror = b(this._on_socket_error, this);
        this.socket.onclose = b(this._on_socket_close, this);
        this.sendPinger = new s(this,window,this.connectOptions.keepAliveInterval);
        this.receivePinger = new s(this,window,this.connectOptions.keepAliveInterval);
        this._connectTimeout = new w(this,window,this.connectOptions.timeout,this._disconnected,[j.CONNECT_TIMEOUT.code, u(j.CONNECT_TIMEOUT)])
    }
    ;
    v.prototype._schedule_message = function(z) {
        this._msg_queue.push(z);
        if (this.connected) {
            this._process_queue()
        }
    }
    ;
    v.prototype.store = function(E, D) {
        var A = {
            type: D.type,
            messageIdentifier: D.messageIdentifier,
            version: 1
        };
        switch (D.type) {
        case o.PUBLISH:
            if (D.pubRecReceived) {
                A.pubRecReceived = true
            }
            A.payloadMessage = {};
            var C = "";
            var B = D.payloadMessage.payloadBytes;
            for (var z = 0; z < B.length; z++) {
                if (B[z] <= 15) {
                    C = C + "0" + B[z].toString(16)
                } else {
                    C = C + B[z].toString(16)
                }
            }
            A.payloadMessage.payloadHex = C;
            A.payloadMessage.qos = D.payloadMessage.qos;
            A.payloadMessage.destinationName = D.payloadMessage.destinationName;
            if (D.payloadMessage.duplicate) {
                A.payloadMessage.duplicate = true
            }
            if (D.payloadMessage.retained) {
                A.payloadMessage.retained = true
            }
            if (E.indexOf("Sent:") == 0) {
                if (D.sequence === undefined) {
                    D.sequence = ++this._sequence
                }
                A.sequence = D.sequence
            }
            break;
        default:
            throw Error(u(j.INVALID_STORED_DATA, [key, A]))
        }
        localStorage.setItem(E + this._localKey + D.messageIdentifier, JSON.stringify(A))
    }
    ;
    v.prototype.restore = function(H) {
        var G = localStorage.getItem(H);
        var F = JSON.parse(G);
        var I = new q(F.type,F);
        switch (F.type) {
        case o.PUBLISH:
            var z = F.payloadMessage.payloadHex;
            var A = new ArrayBuffer((z.length) / 2);
            var D = new Uint8Array(A);
            var B = 0;
            while (z.length >= 2) {
                var E = parseInt(z.substring(0, 2), 16);
                z = z.substring(2, z.length);
                D[B++] = E
            }
            var C = new Paho.MQTT.Message(D);
            C.qos = F.payloadMessage.qos;
            C.destinationName = F.payloadMessage.destinationName;
            if (F.payloadMessage.duplicate) {
                C.duplicate = true
            }
            if (F.payloadMessage.retained) {
                C.retained = true
            }
            I.payloadMessage = C;
            break;
        default:
            throw Error(u(j.INVALID_STORED_DATA, [H, G]))
        }
        if (H.indexOf("Sent:" + this._localKey) == 0) {
            I.payloadMessage.duplicate = true;
            this._sentMessages[I.messageIdentifier] = I
        } else {
            if (H.indexOf("Received:" + this._localKey) == 0) {
                this._receivedMessages[I.messageIdentifier] = I
            }
        }
    }
    ;
    v.prototype._process_queue = function() {
        var A = null;
        var z = this._msg_queue.reverse();
        while ((A = z.pop())) {
            this._socket_send(A);
            if (this._notify_msg_sent[A]) {
                this._notify_msg_sent[A]();
                delete this._notify_msg_sent[A]
            }
        }
    }
    ;
    v.prototype._requires_ack = function(A) {
        var z = Object.keys(this._sentMessages).length;
        if (z > this.maxMessageIdentifier) {
            throw Error("Too many messages:" + z)
        }
        while (this._sentMessages[this._message_identifier] !== undefined) {
            this._message_identifier++
        }
        A.messageIdentifier = this._message_identifier;
        this._sentMessages[A.messageIdentifier] = A;
        if (A.type === o.PUBLISH) {
            this.store("Sent:", A)
        }
        if (this._message_identifier === this.maxMessageIdentifier) {
            this._message_identifier = 1
        }
    }
    ;
    v.prototype._on_socket_open = function() {
        var z = new q(o.CONNECT,this.connectOptions);
        z.clientId = this.clientId;
        this._socket_send(z)
    }
    ;
    v.prototype._on_socket_message = function(B) {
        this._trace("Client._on_socket_message", B.data);
        this.receivePinger.reset();
        var A = this._deframeMessages(B.data);
        for (var z = 0; z < A.length; z += 1) {
            this._handleMessage(A[z])
        }
    }
    ;
    v.prototype._deframeMessages = function(F) {
        var A = new Uint8Array(F);
        if (this.receiveBuffer) {
            var C = new Uint8Array(this.receiveBuffer.length + A.length);
            C.set(this.receiveBuffer);
            C.set(A, this.receiveBuffer.length);
            A = C;
            delete this.receiveBuffer
        }
        try {
            var G = 0;
            var D = [];
            while (G < A.length) {
                var z = g(A, G);
                var E = z[0];
                G = z[1];
                if (E !== null) {
                    D.push(E)
                } else {
                    break
                }
            }
            if (G < A.length) {
                this.receiveBuffer = A.subarray(G)
            }
        } catch (B) {
            this._disconnected(j.INTERNAL_ERROR.code, u(j.INTERNAL_ERROR, [B.message, B.stack.toString()]));
            return
        }
        return D
    }
    ;
    v.prototype._handleMessage = function(I) {
        this._trace("Client._handleMessage", I);
        try {
            switch (I.type) {
            case o.CONNACK:
                this._connectTimeout.cancel();
                if (this.connectOptions.cleanSession) {
                    for (var H in this._sentMessages) {
                        var G = this._sentMessages[H];
                        localStorage.removeItem("Sent:" + this._localKey + G.messageIdentifier)
                    }
                    this._sentMessages = {};
                    for (var H in this._receivedMessages) {
                        var z = this._receivedMessages[H];
                        localStorage.removeItem("Received:" + this._localKey + z.messageIdentifier)
                    }
                    this._receivedMessages = {}
                }
                if (I.returnCode === 0) {
                    this.connected = true;
                    if (this.connectOptions.uris) {
                        this.hostIndex = this.connectOptions.uris.length
                    }
                } else {
                    this._disconnected(j.CONNACK_RETURNCODE.code, u(j.CONNACK_RETURNCODE, [I.returnCode, f[I.returnCode]]));
                    break
                }
                var E = new Array();
                for (var A in this._sentMessages) {
                    if (this._sentMessages.hasOwnProperty(A)) {
                        E.push(this._sentMessages[A])
                    }
                }
                var E = E.sort(function(L, K) {
                    return L.sequence - K.sequence
                });
                for (var C = 0, D = E.length; C < D; C++) {
                    var G = E[C];
                    if (G.type == o.PUBLISH && G.pubRecReceived) {
                        var B = new q(o.PUBREL,{
                            messageIdentifier: G.messageIdentifier
                        });
                        this._schedule_message(B)
                    } else {
                        this._schedule_message(G)
                    }
                }
                if (this.connectOptions.onSuccess) {
                    this.connectOptions.onSuccess({
                        invocationContext: this.connectOptions.invocationContext
                    })
                }
                this._process_queue();
                break;
            case o.PUBLISH:
                this._receivePublish(I);
                break;
            case o.PUBACK:
                var G = this._sentMessages[I.messageIdentifier];
                if (G) {
                    delete this._sentMessages[I.messageIdentifier];
                    localStorage.removeItem("Sent:" + this._localKey + I.messageIdentifier);
                    if (this.onMessageDelivered) {
                        this.onMessageDelivered(G.payloadMessage)
                    }
                }
                break;
            case o.PUBREC:
                var G = this._sentMessages[I.messageIdentifier];
                if (G) {
                    G.pubRecReceived = true;
                    var B = new q(o.PUBREL,{
                        messageIdentifier: I.messageIdentifier
                    });
                    this.store("Sent:", G);
                    this._schedule_message(B)
                }
                break;
            case o.PUBREL:
                var z = this._receivedMessages[I.messageIdentifier];
                localStorage.removeItem("Received:" + this._localKey + I.messageIdentifier);
                if (z) {
                    this._receiveMessage(z);
                    delete this._receivedMessages[I.messageIdentifier]
                }
                var J = new q(o.PUBCOMP,{
                    messageIdentifier: I.messageIdentifier
                });
                this._schedule_message(J);
                break;
            case o.PUBCOMP:
                var G = this._sentMessages[I.messageIdentifier];
                delete this._sentMessages[I.messageIdentifier];
                localStorage.removeItem("Sent:" + this._localKey + I.messageIdentifier);
                if (this.onMessageDelivered) {
                    this.onMessageDelivered(G.payloadMessage)
                }
                break;
            case o.SUBACK:
                var G = this._sentMessages[I.messageIdentifier];
                if (G) {
                    if (G.timeOut) {
                        G.timeOut.cancel()
                    }
                    if (I.returnCode[0] === 128) {
                        if (G.onFailure) {
                            G.onFailure(I.returnCode)
                        }
                    } else {
                        if (G.onSuccess) {
                            G.onSuccess(I.returnCode)
                        }
                    }
                    delete this._sentMessages[I.messageIdentifier]
                }
                break;
            case o.UNSUBACK:
                var G = this._sentMessages[I.messageIdentifier];
                if (G) {
                    if (G.timeOut) {
                        G.timeOut.cancel()
                    }
                    if (G.callback) {
                        G.callback()
                    }
                    delete this._sentMessages[I.messageIdentifier]
                }
                break;
            case o.PINGRESP:
                this.sendPinger.reset();
                break;
            case o.DISCONNECT:
                this._disconnected(j.INVALID_MQTT_MESSAGE_TYPE.code, u(j.INVALID_MQTT_MESSAGE_TYPE, [I.type]));
                break;
            default:
                this._disconnected(j.INVALID_MQTT_MESSAGE_TYPE.code, u(j.INVALID_MQTT_MESSAGE_TYPE, [I.type]))
            }
        } catch (F) {
            this._disconnected(j.INTERNAL_ERROR.code, u(j.INTERNAL_ERROR, [F.message, F.stack.toString()]));
            return
        }
    }
    ;
    v.prototype._on_socket_error = function(z) {
        this._disconnected(j.SOCKET_ERROR.code, u(j.SOCKET_ERROR, [z.data]))
    }
    ;
    v.prototype._on_socket_close = function() {
        this._disconnected(j.SOCKET_CLOSE.code, u(j.SOCKET_CLOSE))
    }
    ;
    v.prototype._socket_send = function(A) {
        if (A.type == 1) {
            var z = this._traceMask(A, "password");
            this._trace("Client._socket_send", z)
        } else {
            this._trace("Client._socket_send", A)
        }
        this.socket.send(A.encode());
        this.sendPinger.reset()
    }
    ;
    v.prototype._receivePublish = function(B) {
        switch (B.payloadMessage.qos) {
        case "undefined":
        case 0:
            this._receiveMessage(B);
            break;
        case 1:
            var z = new q(o.PUBACK,{
                messageIdentifier: B.messageIdentifier
            });
            this._schedule_message(z);
            this._receiveMessage(B);
            break;
        case 2:
            this._receivedMessages[B.messageIdentifier] = B;
            this.store("Received:", B);
            var A = new q(o.PUBREC,{
                messageIdentifier: B.messageIdentifier
            });
            this._schedule_message(A);
            break;
        default:
            throw Error("Invaild qos=" + wireMmessage.payloadMessage.qos)
        }
    }
    ;
    v.prototype._receiveMessage = function(z) {
        if (this.onMessageArrived) {
            this.onMessageArrived(z.payloadMessage)
        }
    }
    ;
    v.prototype._disconnected = function(A, z) {
        this._trace("Client._disconnected", A, z);
        this.sendPinger.cancel();
        this.receivePinger.cancel();
        if (this._connectTimeout) {
            this._connectTimeout.cancel()
        }
        this._msg_queue = [];
        this._notify_msg_sent = {};
        if (this.socket) {
            this.socket.onopen = null;
            this.socket.onmessage = null;
            this.socket.onerror = null;
            this.socket.onclose = null;
            if (this.socket.readyState === 1) {
                this.socket.close()
            }
            delete this.socket
        }
        if (this.connectOptions.uris && this.hostIndex < this.connectOptions.uris.length - 1) {
            this.hostIndex++;
            this._doConnect(this.connectOptions.uris[this.hostIndex])
        } else {
            if (A === undefined) {
                A = j.OK.code;
                z = u(j.OK)
            }
            if (this.connected) {
                this.connected = false;
                if (this.onConnectionLost) {
                    this.onConnectionLost({
                        errorCode: A,
                        errorMessage: z
                    })
                }
            } else {
                if (this.connectOptions.mqttVersion === 4 && this.connectOptions.mqttVersionExplicit === false) {
                    this._trace("Failed to connect V4, dropping back to V3");
                    this.connectOptions.mqttVersion = 3;
                    if (this.connectOptions.uris) {
                        this.hostIndex = 0;
                        this._doConnect(this.connectOptions.uris[0])
                    } else {
                        this._doConnect(this.uri)
                    }
                } else {
                    if (this.connectOptions.onFailure) {
                        this.connectOptions.onFailure({
                            invocationContext: this.connectOptions.invocationContext,
                            errorCode: A,
                            errorMessage: z
                        })
                    }
                }
            }
        }
    }
    ;
    v.prototype._trace = function() {
        if (this.traceFunction) {
            for (var B in arguments) {
                if (typeof arguments[B] !== "undefined") {
                    arguments[B] = JSON.stringify(arguments[B])
                }
            }
            var A = Array.prototype.slice.call(arguments).join("");
            this.traceFunction({
                severity: "Debug",
                message: A
            })
        }
        if (this._traceBuffer !== null) {
            for (var B = 0, z = arguments.length; B < z; B++) {
                if (this._traceBuffer.length == this._MAX_TRACE_ENTRIES) {
                    this._traceBuffer.shift()
                }
                if (B === 0) {
                    this._traceBuffer.push(arguments[B])
                } else {
                    if (typeof arguments[B] === "undefined") {
                        this._traceBuffer.push(arguments[B])
                    } else {
                        this._traceBuffer.push("  " + JSON.stringify(arguments[B]))
                    }
                }
            }
        }
    }
    ;
    v.prototype._traceMask = function(B, A) {
        var C = {};
        for (var z in B) {
            if (B.hasOwnProperty(z)) {
                if (z == A) {
                    C[z] = "******"
                } else {
                    C[z] = B[z]
                }
            }
        }
        return C
    }
    ;
    var p = function(I, C, J, z) {
        var B;
        if (typeof I !== "string") {
            throw new Error(u(j.INVALID_TYPE, [typeof I, "host"]))
        }
        if (arguments.length == 2) {
            z = C;
            B = I;
            var F = B.match(/^(wss?):\/\/((\[(.+)\])|([^\/]+?))(:(\d+))?(\/.*)$/);
            if (F) {
                I = F[4] || F[2];
                C = parseInt(F[7]);
                J = F[8]
            } else {
                throw new Error(u(j.INVALID_ARGUMENT, [I, "host"]))
            }
        } else {
            if (arguments.length == 3) {
                z = J;
                J = "/mqtt"
            }
            if (typeof C !== "number" || C < 0) {
                throw new Error(u(j.INVALID_TYPE, [typeof C, "port"]))
            }
            if (typeof J !== "string") {
                throw new Error(u(j.INVALID_TYPE, [typeof J, "path"]))
            }
            var A = (I.indexOf(":") != -1 && I.slice(0, 1) != "[" && I.slice(-1) != "]");
            B = "ws://" + (A ? "[" + I + "]" : I) + ":" + C + J
        }
        var G = 0;
        for (var E = 0; E < z.length; E++) {
            var H = z.charCodeAt(E);
            if (55296 <= H && H <= 56319) {
                E++
            }
            G++
        }
        if (typeof z !== "string" || G > 65535) {
            throw new Error(u(j.INVALID_ARGUMENT, [z, "clientId"]))
        }
        var D = new v(B,I,C,J,z);
        this._getHost = function() {
            return I
        }
        ;
        this._setHost = function() {
            throw new Error(u(j.UNSUPPORTED_OPERATION))
        }
        ;
        this._getPort = function() {
            return C
        }
        ;
        this._setPort = function() {
            throw new Error(u(j.UNSUPPORTED_OPERATION))
        }
        ;
        this._getPath = function() {
            return J
        }
        ;
        this._setPath = function() {
            throw new Error(u(j.UNSUPPORTED_OPERATION))
        }
        ;
        this._getURI = function() {
            return B
        }
        ;
        this._setURI = function() {
            throw new Error(u(j.UNSUPPORTED_OPERATION))
        }
        ;
        this._getClientId = function() {
            return D.clientId
        }
        ;
        this._setClientId = function() {
            throw new Error(u(j.UNSUPPORTED_OPERATION))
        }
        ;
        this._getOnConnectionLost = function() {
            return D.onConnectionLost
        }
        ;
        this._setOnConnectionLost = function(K) {
            if (typeof K === "function") {
                D.onConnectionLost = K
            } else {
                throw new Error(u(j.INVALID_TYPE, [typeof K, "onConnectionLost"]))
            }
        }
        ;
        this._getOnMessageDelivered = function() {
            return D.onMessageDelivered
        }
        ;
        this._setOnMessageDelivered = function(K) {
            if (typeof K === "function") {
                D.onMessageDelivered = K
            } else {
                throw new Error(u(j.INVALID_TYPE, [typeof K, "onMessageDelivered"]))
            }
        }
        ;
        this._getOnMessageArrived = function() {
            return D.onMessageArrived
        }
        ;
        this._setOnMessageArrived = function(K) {
            if (typeof K === "function") {
                D.onMessageArrived = K
            } else {
                throw new Error(u(j.INVALID_TYPE, [typeof K, "onMessageArrived"]))
            }
        }
        ;
        this._getTrace = function() {
            return D.traceFunction
        }
        ;
        this._setTrace = function(K) {
            if (typeof K === "function") {
                D.traceFunction = K
            } else {
                throw new Error(u(j.INVALID_TYPE, [typeof K, "onTrace"]))
            }
        }
        ;
        this.connect = function(N) {
            N = N || {};
            m(N, {
                timeout: "number",
                userName: "string",
                password: "string",
                willMessage: "object",
                keepAliveInterval: "number",
                cleanSession: "boolean",
                useSSL: "boolean",
                invocationContext: "object",
                onSuccess: "function",
                onFailure: "function",
                hosts: "object",
                ports: "object",
                mqttVersion: "number",
                token: "string"
            });
            if (N.keepAliveInterval === undefined) {
                N.keepAliveInterval = 60
            }
            if (N.mqttVersion > 4 || N.mqttVersion < 3) {
                throw new Error(u(j.INVALID_ARGUMENT, [N.mqttVersion, "connectOptions.mqttVersion"]))
            }
            if (N.mqttVersion === undefined) {
                N.mqttVersionExplicit = false;
                N.mqttVersion = 4
            } else {
                N.mqttVersionExplicit = true
            }
            if (N.password === undefined && N.userName !== undefined) {
                throw new Error(u(j.INVALID_ARGUMENT, [N.password, "connectOptions.password"]))
            }
            if (N.willMessage) {
                if (!(N.willMessage instanceof a)) {
                    throw new Error(u(j.INVALID_TYPE, [N.willMessage, "connectOptions.willMessage"]))
                }
                N.willMessage.stringPayload;
                if (typeof N.willMessage.destinationName === "undefined") {
                    throw new Error(u(j.INVALID_TYPE, [typeof N.willMessage.destinationName, "connectOptions.willMessage.destinationName"]))
                }
            }
            if (typeof N.cleanSession === "undefined") {
                N.cleanSession = true
            }
            if (N.hosts) {
                if (!(N.hosts instanceof Array)) {
                    throw new Error(u(j.INVALID_ARGUMENT, [N.hosts, "connectOptions.hosts"]))
                }
                if (N.hosts.length < 1) {
                    throw new Error(u(j.INVALID_ARGUMENT, [N.hosts, "connectOptions.hosts"]))
                }
                var P = false;
                for (var M = 0; M < N.hosts.length; M++) {
                    if (typeof N.hosts[M] !== "string") {
                        throw new Error(u(j.INVALID_TYPE, [typeof N.hosts[M], "connectOptions.hosts[" + M + "]"]))
                    }
                    if (/^(wss?):\/\/((\[(.+)\])|([^\/]+?))(:(\d+))?(\/.*)$/.test(N.hosts[M])) {
                        if (M == 0) {
                            P = true
                        } else {
                            if (!P) {
                                throw new Error(u(j.INVALID_ARGUMENT, [N.hosts[M], "connectOptions.hosts[" + M + "]"]))
                            }
                        }
                    } else {
                        if (P) {
                            throw new Error(u(j.INVALID_ARGUMENT, [N.hosts[M], "connectOptions.hosts[" + M + "]"]))
                        }
                    }
                }
                if (!P) {
                    if (!N.ports) {
                        throw new Error(u(j.INVALID_ARGUMENT, [N.ports, "connectOptions.ports"]))
                    }
                    if (!(N.ports instanceof Array)) {
                        throw new Error(u(j.INVALID_ARGUMENT, [N.ports, "connectOptions.ports"]))
                    }
                    if (N.hosts.length != N.ports.length) {
                        throw new Error(u(j.INVALID_ARGUMENT, [N.ports, "connectOptions.ports"]))
                    }
                    N.uris = [];
                    for (var M = 0; M < N.hosts.length; M++) {
                        if (typeof N.ports[M] !== "number" || N.ports[M] < 0) {
                            throw new Error(u(j.INVALID_TYPE, [typeof N.ports[M], "connectOptions.ports[" + M + "]"]))
                        }
                        var O = N.hosts[M];
                        var L = N.ports[M];
                        var K = (O.indexOf(":") != -1);
                        B = "ws://" + (K ? "[" + O + "]" : O) + ":" + L + J;
                        N.uris.push(B)
                    }
                } else {
                    N.uris = N.hosts
                }
            }
            D.connect(N)
        }
        ;
        this.subscribe = function(L, K) {
            if (typeof L !== "string") {
                throw new Error("Invalid argument:" + L)
            }
            K = K || {};
            m(K, {
                qos: "number",
                invocationContext: "object",
                onSuccess: "function",
                onFailure: "function",
                timeout: "number"
            });
            if (K.timeout && !K.onFailure) {
                throw new Error("subscribeOptions.timeout specified with no onFailure callback.")
            }
            if (typeof K.qos !== "undefined" && !(K.qos === 0 || K.qos === 1 || K.qos === 2)) {
                throw new Error(u(j.INVALID_ARGUMENT, [K.qos, "subscribeOptions.qos"]))
            }
            D.subscribe(L, K)
        }
        ;
        this.unsubscribe = function(L, K) {
            if (typeof L !== "string") {
                throw new Error("Invalid argument:" + L)
            }
            K = K || {};
            m(K, {
                invocationContext: "object",
                onSuccess: "function",
                onFailure: "function",
                timeout: "number"
            });
            if (K.timeout && !K.onFailure) {
                throw new Error("unsubscribeOptions.timeout specified with no onFailure callback.")
            }
            D.unsubscribe(L, K)
        }
        ;
        this.send = function(L, O, N, K) {
            var M;
            if (arguments.length == 0) {
                throw new Error("Invalid argument.length")
            } else {
                if (arguments.length == 1) {
                    if (!(L instanceof a) && (typeof L !== "string")) {
                        throw new Error("Invalid argument:" + typeof L)
                    }
                    M = L;
                    if (typeof M.destinationName === "undefined") {
                        throw new Error(u(j.INVALID_ARGUMENT, [M.destinationName, "Message.destinationName"]))
                    }
                    D.send(M)
                } else {
                    M = new a(O);
                    M.destinationName = L;
                    if (arguments.length >= 3) {
                        M.qos = N
                    }
                    if (arguments.length >= 4) {
                        M.retained = K
                    }
                    D.send(M)
                }
            }
        }
        ;
        this.disconnect = function() {
            D.disconnect()
        }
        ;
        this.getTraceLog = function() {
            return D.getTraceLog()
        }
        ;
        this.startTrace = function() {
            D.startTrace()
        }
        ;
        this.stopTrace = function() {
            D.stopTrace()
        }
        ;
        this.isConnected = function() {
            return D.connected
        }
    };
    p.prototype = {
        get host() {
            return this._getHost()
        },
        set host(z) {
            this._setHost(z)
        },
        get port() {
            return this._getPort()
        },
        set port(z) {
            this._setPort(z)
        },
        get path() {
            return this._getPath()
        },
        set path(z) {
            this._setPath(z)
        },
        get clientId() {
            return this._getClientId()
        },
        set clientId(z) {
            this._setClientId(z)
        },
        get onConnectionLost() {
            return this._getOnConnectionLost()
        },
        set onConnectionLost(z) {
            this._setOnConnectionLost(z)
        },
        get onMessageDelivered() {
            return this._getOnMessageDelivered()
        },
        set onMessageDelivered(z) {
            this._setOnMessageDelivered(z)
        },
        get onMessageArrived() {
            return this._getOnMessageArrived()
        },
        set onMessageArrived(z) {
            this._setOnMessageArrived(z)
        },
        get trace() {
            return this._getTrace()
        },
        set trace(z) {
            this._setTrace(z)
        }
    };
    var a = function(A) {
        var D;
        if (typeof A === "string" || A instanceof ArrayBuffer || A instanceof Int8Array || A instanceof Uint8Array || A instanceof Int16Array || A instanceof Uint16Array || A instanceof Int32Array || A instanceof Uint32Array || A instanceof Float32Array || A instanceof Float64Array) {
            D = A
        } else {
            throw (u(j.INVALID_ARGUMENT, [A, "newPayload"]))
        }
        this._getPayloadString = function() {
            if (typeof D === "string") {
                return D
            } else {
                return n(D, 0, D.length)
            }
        }
        ;
        this._getPayloadBytes = function() {
            if (typeof D === "string") {
                var F = new ArrayBuffer(c(D));
                var G = new Uint8Array(F);
                i(D, G, 0);
                return G
            } else {
                return D
            }
        }
        ;
        var E = undefined;
        this._getDestinationName = function() {
            return E
        }
        ;
        this._setDestinationName = function(F) {
            if (typeof F === "string") {
                E = F
            } else {
                throw new Error(u(j.INVALID_ARGUMENT, [F, "newDestinationName"]))
            }
        }
        ;
        var B = 0;
        this._getQos = function() {
            return B
        }
        ;
        this._setQos = function(F) {
            if (F === 0 || F === 1 || F === 2) {
                B = F
            } else {
                throw new Error("Invalid argument:" + F)
            }
        }
        ;
        var z = false;
        this._getRetained = function() {
            return z
        }
        ;
        this._setRetained = function(F) {
            if (typeof F === "boolean") {
                z = F
            } else {
                throw new Error(u(j.INVALID_ARGUMENT, [F, "newRetained"]))
            }
        }
        ;
        var C = false;
        this._getDuplicate = function() {
            return C
        }
        ;
        this._setDuplicate = function(F) {
            C = F
        }
    };
    a.prototype = {
        get payloadString() {
            return this._getPayloadString()
        },
        get payloadBytes() {
            return this._getPayloadBytes()
        },
        get destinationName() {
            return this._getDestinationName()
        },
        set destinationName(z) {
            this._setDestinationName(z)
        },
        get qos() {
            return this._getQos()
        },
        set qos(z) {
            this._setQos(z)
        },
        get retained() {
            return this._getRetained()
        },
        set retained(z) {
            this._setRetained(z)
        },
        get duplicate() {
            return this._getDuplicate()
        },
        set duplicate(z) {
            this._setDuplicate(z)
        }
    };
    return {
        Client: p,
        Message: a
    }
}
)(window);
(function(b, a) {
    if (typeof define === "function" && define.amd) {
        define(["/v2/web/boss/js/module/chat-long.js"], function() {
            (b.dcodeIO = b.dcodeIO || {})["ByteBuffer"] = a(b.dcodeIO["Long"])
        })
    } else {
        if (typeof require === "function" && typeof module === "object" && module && module.exports) {
            module.exports = (function() {
                var c;
                try {
                    c = require("long")
                } catch (d) {}
                return a(c)
            }
            )()
        } else {
            (b.dcodeIO = b.dcodeIO || {})["ByteBuffer"] = a(b.dcodeIO["Long"])
        }
    }
}
)(this, function(f) {
    var i = function(l, n, m) {
        if (typeof l === "undefined") {
            l = i.DEFAULT_CAPACITY
        }
        if (typeof n === "undefined") {
            n = i.DEFAULT_ENDIAN
        }
        if (typeof m === "undefined") {
            m = i.DEFAULT_NOASSERT
        }
        if (!m) {
            l = l | 0;
            if (l < 0) {
                throw RangeError("Illegal capacity")
            }
            n = !!n;
            m = !!m
        }
        this.buffer = l === 0 ? k : new ArrayBuffer(l);
        this.view = l === 0 ? null : new Uint8Array(this.buffer);
        this.offset = 0;
        this.markedOffset = -1;
        this.limit = l;
        this.littleEndian = n;
        this.noAssert = m
    };
    i.VERSION = "5.0.1";
    i.LITTLE_ENDIAN = true;
    i.BIG_ENDIAN = false;
    i.DEFAULT_CAPACITY = 16;
    i.DEFAULT_ENDIAN = i.BIG_ENDIAN;
    i.DEFAULT_NOASSERT = false;
    i.Long = f || null;
    var g = i.prototype;
    g.__isByteBuffer__;
    Object.defineProperty(g, "__isByteBuffer__", {
        value: true,
        enumerable: false,
        configurable: false
    });
    var k = new ArrayBuffer(0);
    var h = String.fromCharCode;
    function a(m) {
        var l = 0;
        return function() {
            return l < m.length ? m.charCodeAt(l++) : null
        }
    }
    function b() {
        var l = []
          , m = [];
        return function() {
            if (arguments.length === 0) {
                return m.join("") + h.apply(String, l)
            }
            if (l.length + arguments.length > 1024) {
                m.push(h.apply(String, l)),
                l.length = 0
            }
            Array.prototype.push.apply(l, arguments)
        }
    }
    i.accessor = function() {
        return Uint8Array
    }
    ;
    i.allocate = function(l, n, m) {
        return new i(l,n,m)
    }
    ;
    i.concat = function(u, n, m, t) {
        if (typeof n === "boolean" || typeof n !== "string") {
            t = m;
            m = n;
            n = undefined
        }
        var l = 0;
        for (var r = 0, q = u.length, o; r < q; ++r) {
            if (!i.isByteBuffer(u[r])) {
                u[r] = i.wrap(u[r], n)
            }
            o = u[r].limit - u[r].offset;
            if (o > 0) {
                l += o
            }
        }
        if (l === 0) {
            return new i(0,m,t)
        }
        var s = new i(l,m,t), p;
        r = 0;
        while (r < q) {
            p = u[r++];
            o = p.limit - p.offset;
            if (o <= 0) {
                continue
            }
            s.view.set(p.view.subarray(p.offset, p.limit), s.offset);
            s.offset += o
        }
        s.limit = s.offset;
        s.offset = 0;
        return s
    }
    ;
    i.isByteBuffer = function(l) {
        return (l && l.__isByteBuffer__) === true
    }
    ;
    i.type = function() {
        return ArrayBuffer
    }
    ;
    i.wrap = function(l, n, p, o) {
        if (typeof n !== "string") {
            o = p;
            p = n;
            n = undefined
        }
        if (typeof l === "string") {
            if (typeof n === "undefined") {
                n = "utf8"
            }
            switch (n) {
            case "base64":
                return i.fromBase64(l, p);
            case "hex":
                return i.fromHex(l, p);
            case "binary":
                return i.fromBinary(l, p);
            case "utf8":
                return i.fromUTF8(l, p);
            case "debug":
                return i.fromDebug(l, p);
            default:
                throw Error("Unsupported encoding: " + n)
            }
        }
        if (l === null || typeof l !== "object") {
            throw TypeError("Illegal buffer")
        }
        var q;
        if (i.isByteBuffer(l)) {
            q = g.clone.call(l);
            q.markedOffset = -1;
            return q
        }
        if (l instanceof Uint8Array) {
            q = new i(0,p,o);
            if (l.length > 0) {
                q.buffer = l.buffer;
                q.offset = l.byteOffset;
                q.limit = l.byteOffset + l.byteLength;
                q.view = new Uint8Array(l.buffer)
            }
        } else {
            if (l instanceof ArrayBuffer) {
                q = new i(0,p,o);
                if (l.byteLength > 0) {
                    q.buffer = l;
                    q.offset = 0;
                    q.limit = l.byteLength;
                    q.view = l.byteLength > 0 ? new Uint8Array(l) : null
                }
            } else {
                if (Object.prototype.toString.call(l) === "[object Array]") {
                    q = new i(l.length,p,o);
                    q.limit = l.length;
                    for (var m = 0; m < l.length; ++m) {
                        q.view[m] = l[m]
                    }
                } else {
                    throw TypeError("Illegal buffer")
                }
            }
        }
        return q
    }
    ;
    g.writeBitSet = function(s, q) {
        var l = typeof q === "undefined";
        if (l) {
            q = this.offset
        }
        if (!this.noAssert) {
            if (!(s instanceof Array)) {
                throw TypeError("Illegal BitSet: Not an array")
            }
            if (typeof q !== "number" || q % 1 !== 0) {
                throw TypeError("Illegal offset: " + q + " (not an integer)")
            }
            q >>>= 0;
            if (q < 0 || q + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + q + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        var n = q, t = s.length, u = (t >> 3), r = 0, p;
        q += this.writeVarint32(t, q);
        while (u--) {
            p = (!!s[r++] & 1) | ((!!s[r++] & 1) << 1) | ((!!s[r++] & 1) << 2) | ((!!s[r++] & 1) << 3) | ((!!s[r++] & 1) << 4) | ((!!s[r++] & 1) << 5) | ((!!s[r++] & 1) << 6) | ((!!s[r++] & 1) << 7);
            this.writeByte(p, q++)
        }
        if (r < t) {
            var o = 0;
            p = 0;
            while (r < t) {
                p = p | ((!!s[r++] & 1) << (o++))
            }
            this.writeByte(p, q++)
        }
        if (l) {
            this.offset = q;
            return this
        }
        return q - n
    }
    ;
    g.readBitSet = function(p) {
        var l = typeof p === "undefined";
        if (l) {
            p = this.offset
        }
        var q = this.readVarint32(p), t = q.value, u = (t >> 3), r = 0, s = [], o;
        p += q.length;
        while (u--) {
            o = this.readByte(p++);
            s[r++] = !!(o & 1);
            s[r++] = !!(o & 2);
            s[r++] = !!(o & 4);
            s[r++] = !!(o & 8);
            s[r++] = !!(o & 16);
            s[r++] = !!(o & 32);
            s[r++] = !!(o & 64);
            s[r++] = !!(o & 128)
        }
        if (r < t) {
            var n = 0;
            o = this.readByte(p++);
            while (r < t) {
                s[r++] = !!((o >> (n++)) & 1)
            }
        }
        if (l) {
            this.offset = p
        }
        return s
    }
    ;
    g.readBytes = function(l, o) {
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + l > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + l + ") <= " + this.buffer.byteLength)
            }
        }
        var n = this.slice(o, o + l);
        if (m) {
            this.offset += l
        }
        return n
    }
    ;
    g.writeBytes = g.append;
    g.writeInt8 = function(n, o) {
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal value: " + n + " (not an integer)")
            }
            n |= 0;
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        o += 1;
        var l = this.buffer.byteLength;
        if (o > l) {
            this.resize((l *= 2) > o ? l : o)
        }
        o -= 1;
        this.view[o] = n;
        if (m) {
            this.offset += 1
        }
        return this
    }
    ;
    g.writeByte = g.writeInt8;
    g.readInt8 = function(n) {
        var m = typeof n === "undefined";
        if (m) {
            n = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal offset: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (n < 0 || n + 1 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + n + " (+" + 1 + ") <= " + this.buffer.byteLength)
            }
        }
        var l = this.view[n];
        if ((l & 128) === 128) {
            l = -(255 - l + 1)
        }
        if (m) {
            this.offset += 1
        }
        return l
    }
    ;
    g.readByte = g.readInt8;
    g.writeUint8 = function(n, o) {
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal value: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        o += 1;
        var l = this.buffer.byteLength;
        if (o > l) {
            this.resize((l *= 2) > o ? l : o)
        }
        o -= 1;
        this.view[o] = n;
        if (m) {
            this.offset += 1
        }
        return this
    }
    ;
    g.writeUInt8 = g.writeUint8;
    g.readUint8 = function(n) {
        var m = typeof n === "undefined";
        if (m) {
            n = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal offset: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (n < 0 || n + 1 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + n + " (+" + 1 + ") <= " + this.buffer.byteLength)
            }
        }
        var l = this.view[n];
        if (m) {
            this.offset += 1
        }
        return l
    }
    ;
    g.readUInt8 = g.readUint8;
    g.writeInt16 = function(n, o) {
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal value: " + n + " (not an integer)")
            }
            n |= 0;
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        o += 2;
        var l = this.buffer.byteLength;
        if (o > l) {
            this.resize((l *= 2) > o ? l : o)
        }
        o -= 2;
        if (this.littleEndian) {
            this.view[o + 1] = (n & 65280) >>> 8;
            this.view[o] = n & 255
        } else {
            this.view[o] = (n & 65280) >>> 8;
            this.view[o + 1] = n & 255
        }
        if (m) {
            this.offset += 2
        }
        return this
    }
    ;
    g.writeShort = g.writeInt16;
    g.readInt16 = function(n) {
        var m = typeof n === "undefined";
        if (m) {
            n = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal offset: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (n < 0 || n + 2 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + n + " (+" + 2 + ") <= " + this.buffer.byteLength)
            }
        }
        var l = 0;
        if (this.littleEndian) {
            l = this.view[n];
            l |= this.view[n + 1] << 8
        } else {
            l = this.view[n] << 8;
            l |= this.view[n + 1]
        }
        if ((l & 32768) === 32768) {
            l = -(65535 - l + 1)
        }
        if (m) {
            this.offset += 2
        }
        return l
    }
    ;
    g.readShort = g.readInt16;
    g.writeUint16 = function(n, o) {
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal value: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        o += 2;
        var l = this.buffer.byteLength;
        if (o > l) {
            this.resize((l *= 2) > o ? l : o)
        }
        o -= 2;
        if (this.littleEndian) {
            this.view[o + 1] = (n & 65280) >>> 8;
            this.view[o] = n & 255
        } else {
            this.view[o] = (n & 65280) >>> 8;
            this.view[o + 1] = n & 255
        }
        if (m) {
            this.offset += 2
        }
        return this
    }
    ;
    g.writeUInt16 = g.writeUint16;
    g.readUint16 = function(n) {
        var m = typeof n === "undefined";
        if (m) {
            n = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal offset: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (n < 0 || n + 2 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + n + " (+" + 2 + ") <= " + this.buffer.byteLength)
            }
        }
        var l = 0;
        if (this.littleEndian) {
            l = this.view[n];
            l |= this.view[n + 1] << 8
        } else {
            l = this.view[n] << 8;
            l |= this.view[n + 1]
        }
        if (m) {
            this.offset += 2
        }
        return l
    }
    ;
    g.readUInt16 = g.readUint16;
    g.writeInt32 = function(n, o) {
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal value: " + n + " (not an integer)")
            }
            n |= 0;
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        o += 4;
        var l = this.buffer.byteLength;
        if (o > l) {
            this.resize((l *= 2) > o ? l : o)
        }
        o -= 4;
        if (this.littleEndian) {
            this.view[o + 3] = (n >>> 24) & 255;
            this.view[o + 2] = (n >>> 16) & 255;
            this.view[o + 1] = (n >>> 8) & 255;
            this.view[o] = n & 255
        } else {
            this.view[o] = (n >>> 24) & 255;
            this.view[o + 1] = (n >>> 16) & 255;
            this.view[o + 2] = (n >>> 8) & 255;
            this.view[o + 3] = n & 255
        }
        if (m) {
            this.offset += 4
        }
        return this
    }
    ;
    g.writeInt = g.writeInt32;
    g.readInt32 = function(n) {
        var m = typeof n === "undefined";
        if (m) {
            n = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal offset: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (n < 0 || n + 4 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + n + " (+" + 4 + ") <= " + this.buffer.byteLength)
            }
        }
        var l = 0;
        if (this.littleEndian) {
            l = this.view[n + 2] << 16;
            l |= this.view[n + 1] << 8;
            l |= this.view[n];
            l += this.view[n + 3] << 24 >>> 0
        } else {
            l = this.view[n + 1] << 16;
            l |= this.view[n + 2] << 8;
            l |= this.view[n + 3];
            l += this.view[n] << 24 >>> 0
        }
        l |= 0;
        if (m) {
            this.offset += 4
        }
        return l
    }
    ;
    g.readInt = g.readInt32;
    g.writeUint32 = function(n, o) {
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal value: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        o += 4;
        var l = this.buffer.byteLength;
        if (o > l) {
            this.resize((l *= 2) > o ? l : o)
        }
        o -= 4;
        if (this.littleEndian) {
            this.view[o + 3] = (n >>> 24) & 255;
            this.view[o + 2] = (n >>> 16) & 255;
            this.view[o + 1] = (n >>> 8) & 255;
            this.view[o] = n & 255
        } else {
            this.view[o] = (n >>> 24) & 255;
            this.view[o + 1] = (n >>> 16) & 255;
            this.view[o + 2] = (n >>> 8) & 255;
            this.view[o + 3] = n & 255
        }
        if (m) {
            this.offset += 4
        }
        return this
    }
    ;
    g.writeUInt32 = g.writeUint32;
    g.readUint32 = function(n) {
        var m = typeof n === "undefined";
        if (m) {
            n = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal offset: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (n < 0 || n + 4 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + n + " (+" + 4 + ") <= " + this.buffer.byteLength)
            }
        }
        var l = 0;
        if (this.littleEndian) {
            l = this.view[n + 2] << 16;
            l |= this.view[n + 1] << 8;
            l |= this.view[n];
            l += this.view[n + 3] << 24 >>> 0
        } else {
            l = this.view[n + 1] << 16;
            l |= this.view[n + 2] << 8;
            l |= this.view[n + 3];
            l += this.view[n] << 24 >>> 0
        }
        if (m) {
            this.offset += 4
        }
        return l
    }
    ;
    g.readUInt32 = g.readUint32;
    if (f) {
        g.writeInt64 = function(o, p) {
            var n = typeof p === "undefined";
            if (n) {
                p = this.offset
            }
            if (!this.noAssert) {
                if (typeof o === "number") {
                    o = f.fromNumber(o)
                } else {
                    if (typeof o === "string") {
                        o = f.fromString(o)
                    } else {
                        if (!(o && o instanceof f)) {
                            throw TypeError("Illegal value: " + o + " (not an integer or Long)")
                        }
                    }
                }
                if (typeof p !== "number" || p % 1 !== 0) {
                    throw TypeError("Illegal offset: " + p + " (not an integer)")
                }
                p >>>= 0;
                if (p < 0 || p + 0 > this.buffer.byteLength) {
                    throw RangeError("Illegal offset: 0 <= " + p + " (+" + 0 + ") <= " + this.buffer.byteLength)
                }
            }
            if (typeof o === "number") {
                o = f.fromNumber(o)
            } else {
                if (typeof o === "string") {
                    o = f.fromString(o)
                }
            }
            p += 8;
            var q = this.buffer.byteLength;
            if (p > q) {
                this.resize((q *= 2) > p ? q : p)
            }
            p -= 8;
            var m = o.low
              , l = o.high;
            if (this.littleEndian) {
                this.view[p + 3] = (m >>> 24) & 255;
                this.view[p + 2] = (m >>> 16) & 255;
                this.view[p + 1] = (m >>> 8) & 255;
                this.view[p] = m & 255;
                p += 4;
                this.view[p + 3] = (l >>> 24) & 255;
                this.view[p + 2] = (l >>> 16) & 255;
                this.view[p + 1] = (l >>> 8) & 255;
                this.view[p] = l & 255
            } else {
                this.view[p] = (l >>> 24) & 255;
                this.view[p + 1] = (l >>> 16) & 255;
                this.view[p + 2] = (l >>> 8) & 255;
                this.view[p + 3] = l & 255;
                p += 4;
                this.view[p] = (m >>> 24) & 255;
                this.view[p + 1] = (m >>> 16) & 255;
                this.view[p + 2] = (m >>> 8) & 255;
                this.view[p + 3] = m & 255
            }
            if (n) {
                this.offset += 8
            }
            return this
        }
        ;
        g.writeLong = g.writeInt64;
        g.readInt64 = function(p) {
            var o = typeof p === "undefined";
            if (o) {
                p = this.offset
            }
            if (!this.noAssert) {
                if (typeof p !== "number" || p % 1 !== 0) {
                    throw TypeError("Illegal offset: " + p + " (not an integer)")
                }
                p >>>= 0;
                if (p < 0 || p + 8 > this.buffer.byteLength) {
                    throw RangeError("Illegal offset: 0 <= " + p + " (+" + 8 + ") <= " + this.buffer.byteLength)
                }
            }
            var m = 0
              , l = 0;
            if (this.littleEndian) {
                m = this.view[p + 2] << 16;
                m |= this.view[p + 1] << 8;
                m |= this.view[p];
                m += this.view[p + 3] << 24 >>> 0;
                p += 4;
                l = this.view[p + 2] << 16;
                l |= this.view[p + 1] << 8;
                l |= this.view[p];
                l += this.view[p + 3] << 24 >>> 0
            } else {
                l = this.view[p + 1] << 16;
                l |= this.view[p + 2] << 8;
                l |= this.view[p + 3];
                l += this.view[p] << 24 >>> 0;
                p += 4;
                m = this.view[p + 1] << 16;
                m |= this.view[p + 2] << 8;
                m |= this.view[p + 3];
                m += this.view[p] << 24 >>> 0
            }
            var n = new f(m,l,false);
            if (o) {
                this.offset += 8
            }
            return n
        }
        ;
        g.readLong = g.readInt64;
        g.writeUint64 = function(o, q) {
            var n = typeof q === "undefined";
            if (n) {
                q = this.offset
            }
            if (!this.noAssert) {
                if (typeof o === "number") {
                    o = f.fromNumber(o)
                } else {
                    if (typeof o === "string") {
                        o = f.fromString(o)
                    } else {
                        if (!(o && o instanceof f)) {
                            throw TypeError("Illegal value: " + o + " (not an integer or Long)")
                        }
                    }
                }
                if (typeof q !== "number" || q % 1 !== 0) {
                    throw TypeError("Illegal offset: " + q + " (not an integer)")
                }
                q >>>= 0;
                if (q < 0 || q + 0 > this.buffer.byteLength) {
                    throw RangeError("Illegal offset: 0 <= " + q + " (+" + 0 + ") <= " + this.buffer.byteLength)
                }
            }
            if (typeof o === "number") {
                o = f.fromNumber(o)
            } else {
                if (typeof o === "string") {
                    o = f.fromString(o)
                }
            }
            q += 8;
            var p = this.buffer.byteLength;
            if (q > p) {
                this.resize((p *= 2) > q ? p : q)
            }
            q -= 8;
            var m = o.low
              , l = o.high;
            if (this.littleEndian) {
                this.view[q + 3] = (m >>> 24) & 255;
                this.view[q + 2] = (m >>> 16) & 255;
                this.view[q + 1] = (m >>> 8) & 255;
                this.view[q] = m & 255;
                q += 4;
                this.view[q + 3] = (l >>> 24) & 255;
                this.view[q + 2] = (l >>> 16) & 255;
                this.view[q + 1] = (l >>> 8) & 255;
                this.view[q] = l & 255
            } else {
                this.view[q] = (l >>> 24) & 255;
                this.view[q + 1] = (l >>> 16) & 255;
                this.view[q + 2] = (l >>> 8) & 255;
                this.view[q + 3] = l & 255;
                q += 4;
                this.view[q] = (m >>> 24) & 255;
                this.view[q + 1] = (m >>> 16) & 255;
                this.view[q + 2] = (m >>> 8) & 255;
                this.view[q + 3] = m & 255
            }
            if (n) {
                this.offset += 8
            }
            return this
        }
        ;
        g.writeUInt64 = g.writeUint64;
        g.readUint64 = function(p) {
            var o = typeof p === "undefined";
            if (o) {
                p = this.offset
            }
            if (!this.noAssert) {
                if (typeof p !== "number" || p % 1 !== 0) {
                    throw TypeError("Illegal offset: " + p + " (not an integer)")
                }
                p >>>= 0;
                if (p < 0 || p + 8 > this.buffer.byteLength) {
                    throw RangeError("Illegal offset: 0 <= " + p + " (+" + 8 + ") <= " + this.buffer.byteLength)
                }
            }
            var m = 0
              , l = 0;
            if (this.littleEndian) {
                m = this.view[p + 2] << 16;
                m |= this.view[p + 1] << 8;
                m |= this.view[p];
                m += this.view[p + 3] << 24 >>> 0;
                p += 4;
                l = this.view[p + 2] << 16;
                l |= this.view[p + 1] << 8;
                l |= this.view[p];
                l += this.view[p + 3] << 24 >>> 0
            } else {
                l = this.view[p + 1] << 16;
                l |= this.view[p + 2] << 8;
                l |= this.view[p + 3];
                l += this.view[p] << 24 >>> 0;
                p += 4;
                m = this.view[p + 1] << 16;
                m |= this.view[p + 2] << 8;
                m |= this.view[p + 3];
                m += this.view[p] << 24 >>> 0
            }
            var n = new f(m,l,true);
            if (o) {
                this.offset += 8
            }
            return n
        }
        ;
        g.readUInt64 = g.readUint64
    }
    function d(t, r, o, n, w) {
        var x, q, p = w * 8 - n - 1, v = (1 << p) - 1, l = v >> 1, z = -7, u = o ? (w - 1) : 0, y = o ? -1 : 1, A = t[r + u];
        u += y;
        x = A & ((1 << (-z)) - 1);
        A >>= (-z);
        z += p;
        for (; z > 0; x = x * 256 + t[r + u],
        u += y,
        z -= 8) {}
        q = x & ((1 << (-z)) - 1);
        x >>= (-z);
        z += n;
        for (; z > 0; q = q * 256 + t[r + u],
        u += y,
        z -= 8) {}
        if (x === 0) {
            x = 1 - l
        } else {
            if (x === v) {
                return q ? NaN : ((A ? -1 : 1) * Infinity)
            } else {
                q = q + Math.pow(2, n);
                x = x - l
            }
        }
        return (A ? -1 : 1) * q * Math.pow(2, x - n)
    }
    function e(u, B, t, o, n, x) {
        var y, q, A, p = x * 8 - n - 1, w = (1 << p) - 1, l = w >> 1, r = (n === 23 ? Math.pow(2, -24) - Math.pow(2, -77) : 0), v = o ? 0 : (x - 1), z = o ? 1 : -1, C = B < 0 || (B === 0 && 1 / B < 0) ? 1 : 0;
        B = Math.abs(B);
        if (isNaN(B) || B === Infinity) {
            q = isNaN(B) ? 1 : 0;
            y = w
        } else {
            y = Math.floor(Math.log(B) / Math.LN2);
            if (B * (A = Math.pow(2, -y)) < 1) {
                y--;
                A *= 2
            }
            if (y + l >= 1) {
                B += r / A
            } else {
                B += r * Math.pow(2, 1 - l)
            }
            if (B * A >= 2) {
                y++;
                A /= 2
            }
            if (y + l >= w) {
                q = 0;
                y = w
            } else {
                if (y + l >= 1) {
                    q = (B * A - 1) * Math.pow(2, n);
                    y = y + l
                } else {
                    q = B * Math.pow(2, l - 1) * Math.pow(2, n);
                    y = 0
                }
            }
        }
        for (; n >= 8; u[t + v] = q & 255,
        v += z,
        q /= 256,
        n -= 8) {}
        y = (y << n) | q;
        p += n;
        for (; p > 0; u[t + v] = y & 255,
        v += z,
        y /= 256,
        p -= 8) {}
        u[t + v - z] |= C * 128
    }
    g.writeFloat32 = function(m, o) {
        var l = typeof o === "undefined";
        if (l) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof m !== "number") {
                throw TypeError("Illegal value: " + m + " (not a number)")
            }
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        o += 4;
        var n = this.buffer.byteLength;
        if (o > n) {
            this.resize((n *= 2) > o ? n : o)
        }
        o -= 4;
        e(this.view, m, o, this.littleEndian, 23, 4);
        if (l) {
            this.offset += 4
        }
        return this
    }
    ;
    g.writeFloat = g.writeFloat32;
    g.readFloat32 = function(n) {
        var m = typeof n === "undefined";
        if (m) {
            n = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal offset: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (n < 0 || n + 4 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + n + " (+" + 4 + ") <= " + this.buffer.byteLength)
            }
        }
        var l = d(this.view, n, this.littleEndian, 23, 4);
        if (m) {
            this.offset += 4
        }
        return l
    }
    ;
    g.readFloat = g.readFloat32;
    g.writeFloat64 = function(n, o) {
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number") {
                throw TypeError("Illegal value: " + n + " (not a number)")
            }
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        o += 8;
        var l = this.buffer.byteLength;
        if (o > l) {
            this.resize((l *= 2) > o ? l : o)
        }
        o -= 8;
        e(this.view, n, o, this.littleEndian, 52, 8);
        if (m) {
            this.offset += 8
        }
        return this
    }
    ;
    g.writeDouble = g.writeFloat64;
    g.readFloat64 = function(n) {
        var m = typeof n === "undefined";
        if (m) {
            n = this.offset
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal offset: " + n + " (not an integer)")
            }
            n >>>= 0;
            if (n < 0 || n + 8 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + n + " (+" + 8 + ") <= " + this.buffer.byteLength)
            }
        }
        var l = d(this.view, n, this.littleEndian, 52, 8);
        if (m) {
            this.offset += 8
        }
        return l
    }
    ;
    g.readDouble = g.readFloat64;
    i.MAX_VARINT32_BYTES = 5;
    i.calculateVarint32 = function(l) {
        l = l >>> 0;
        if (l < 1 << 7) {
            return 1
        } else {
            if (l < 1 << 14) {
                return 2
            } else {
                if (l < 1 << 21) {
                    return 3
                } else {
                    if (l < 1 << 28) {
                        return 4
                    } else {
                        return 5
                    }
                }
            }
        }
    }
    ;
    i.zigZagEncode32 = function(l) {
        return (((l |= 0) << 1) ^ (l >> 31)) >>> 0
    }
    ;
    i.zigZagDecode32 = function(l) {
        return ((l >>> 1) ^ -(l & 1)) | 0
    }
    ;
    g.writeVarint32 = function(p, q) {
        var o = typeof q === "undefined";
        if (o) {
            q = this.offset
        }
        if (!this.noAssert) {
            if (typeof p !== "number" || p % 1 !== 0) {
                throw TypeError("Illegal value: " + p + " (not an integer)")
            }
            p |= 0;
            if (typeof q !== "number" || q % 1 !== 0) {
                throw TypeError("Illegal offset: " + q + " (not an integer)")
            }
            q >>>= 0;
            if (q < 0 || q + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + q + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        var m = i.calculateVarint32(p), l;
        q += m;
        var n = this.buffer.byteLength;
        if (q > n) {
            this.resize((n *= 2) > q ? n : q)
        }
        q -= m;
        p >>>= 0;
        while (p >= 128) {
            l = (p & 127) | 128;
            this.view[q++] = l;
            p >>>= 7
        }
        this.view[q++] = p;
        if (o) {
            this.offset = q;
            return this
        }
        return m
    }
    ;
    g.writeVarint32ZigZag = function(l, m) {
        return this.writeVarint32(i.zigZagEncode32(l), m)
    }
    ;
    g.readVarint32 = function(p) {
        var o = typeof p === "undefined";
        if (o) {
            p = this.offset
        }
        if (!this.noAssert) {
            if (typeof p !== "number" || p % 1 !== 0) {
                throw TypeError("Illegal offset: " + p + " (not an integer)")
            }
            p >>>= 0;
            if (p < 0 || p + 1 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + p + " (+" + 1 + ") <= " + this.buffer.byteLength)
            }
        }
        var q = 0, n = 0 >>> 0, l;
        do {
            if (!this.noAssert && p > this.limit) {
                var m = Error("Truncated");
                m.truncated = true;
                throw m
            }
            l = this.view[p++];
            if (q < 5) {
                n |= (l & 127) << (7 * q)
            }
            ++q
        } while ((l & 128) !== 0);
        n |= 0;
        if (o) {
            this.offset = p;
            return n
        }
        return {
            value: n,
            length: q
        }
    }
    ;
    g.readVarint32ZigZag = function(m) {
        var l = this.readVarint32(m);
        if (typeof l === "object") {
            l.value = i.zigZagDecode32(l.value)
        } else {
            l = i.zigZagDecode32(l)
        }
        return l
    }
    ;
    if (f) {
        i.MAX_VARINT64_BYTES = 10;
        i.calculateVarint64 = function(m) {
            if (typeof m === "number") {
                m = f.fromNumber(m)
            } else {
                if (typeof m === "string") {
                    m = f.fromString(m)
                }
            }
            var o = m.toInt() >>> 0
              , n = m.shiftRightUnsigned(28).toInt() >>> 0
              , l = m.shiftRightUnsigned(56).toInt() >>> 0;
            if (l == 0) {
                if (n == 0) {
                    if (o < 1 << 14) {
                        return o < 1 << 7 ? 1 : 2
                    } else {
                        return o < 1 << 21 ? 3 : 4
                    }
                } else {
                    if (n < 1 << 14) {
                        return n < 1 << 7 ? 5 : 6
                    } else {
                        return n < 1 << 21 ? 7 : 8
                    }
                }
            } else {
                return l < 1 << 7 ? 9 : 10
            }
        }
        ;
        i.zigZagEncode64 = function(l) {
            if (typeof l === "number") {
                l = f.fromNumber(l, false)
            } else {
                if (typeof l === "string") {
                    l = f.fromString(l, false)
                } else {
                    if (l.unsigned !== false) {
                        l = l.toSigned()
                    }
                }
            }
            return l.shiftLeft(1).xor(l.shiftRight(63)).toUnsigned()
        }
        ;
        i.zigZagDecode64 = function(l) {
            if (typeof l === "number") {
                l = f.fromNumber(l, false)
            } else {
                if (typeof l === "string") {
                    l = f.fromString(l, false)
                } else {
                    if (l.unsigned !== false) {
                        l = l.toSigned()
                    }
                }
            }
            return l.shiftRightUnsigned(1).xor(l.and(f.ONE).toSigned().negate()).toSigned()
        }
        ;
        g.writeVarint64 = function(p, s) {
            var o = typeof s === "undefined";
            if (o) {
                s = this.offset
            }
            if (!this.noAssert) {
                if (typeof p === "number") {
                    p = f.fromNumber(p)
                } else {
                    if (typeof p === "string") {
                        p = f.fromString(p)
                    } else {
                        if (!(p && p instanceof f)) {
                            throw TypeError("Illegal value: " + p + " (not an integer or Long)")
                        }
                    }
                }
                if (typeof s !== "number" || s % 1 !== 0) {
                    throw TypeError("Illegal offset: " + s + " (not an integer)")
                }
                s >>>= 0;
                if (s < 0 || s + 0 > this.buffer.byteLength) {
                    throw RangeError("Illegal offset: 0 <= " + s + " (+" + 0 + ") <= " + this.buffer.byteLength)
                }
            }
            if (typeof p === "number") {
                p = f.fromNumber(p, false)
            } else {
                if (typeof p === "string") {
                    p = f.fromString(p, false)
                } else {
                    if (p.unsigned !== false) {
                        p = p.toSigned()
                    }
                }
            }
            var l = i.calculateVarint64(p)
              , r = p.toInt() >>> 0
              , q = p.shiftRightUnsigned(28).toInt() >>> 0
              , n = p.shiftRightUnsigned(56).toInt() >>> 0;
            s += l;
            var m = this.buffer.byteLength;
            if (s > m) {
                this.resize((m *= 2) > s ? m : s)
            }
            s -= l;
            switch (l) {
            case 10:
                this.view[s + 9] = (n >>> 7) & 1;
            case 9:
                this.view[s + 8] = l !== 9 ? (n) | 128 : (n) & 127;
            case 8:
                this.view[s + 7] = l !== 8 ? (q >>> 21) | 128 : (q >>> 21) & 127;
            case 7:
                this.view[s + 6] = l !== 7 ? (q >>> 14) | 128 : (q >>> 14) & 127;
            case 6:
                this.view[s + 5] = l !== 6 ? (q >>> 7) | 128 : (q >>> 7) & 127;
            case 5:
                this.view[s + 4] = l !== 5 ? (q) | 128 : (q) & 127;
            case 4:
                this.view[s + 3] = l !== 4 ? (r >>> 21) | 128 : (r >>> 21) & 127;
            case 3:
                this.view[s + 2] = l !== 3 ? (r >>> 14) | 128 : (r >>> 14) & 127;
            case 2:
                this.view[s + 1] = l !== 2 ? (r >>> 7) | 128 : (r >>> 7) & 127;
            case 1:
                this.view[s] = l !== 1 ? (r) | 128 : (r) & 127
            }
            if (o) {
                this.offset += l;
                return this
            } else {
                return l
            }
        }
        ;
        g.writeVarint64ZigZag = function(l, m) {
            return this.writeVarint64(i.zigZagEncode64(l), m)
        }
        ;
        g.readVarint64 = function(r) {
            var o = typeof r === "undefined";
            if (o) {
                r = this.offset
            }
            if (!this.noAssert) {
                if (typeof r !== "number" || r % 1 !== 0) {
                    throw TypeError("Illegal offset: " + r + " (not an integer)")
                }
                r >>>= 0;
                if (r < 0 || r + 1 > this.buffer.byteLength) {
                    throw RangeError("Illegal offset: 0 <= " + r + " (+" + 1 + ") <= " + this.buffer.byteLength)
                }
            }
            var s = r
              , q = 0
              , p = 0
              , n = 0
              , l = 0;
            l = this.view[r++];
            q = (l & 127);
            if (l & 128) {
                l = this.view[r++];
                q |= (l & 127) << 7;
                if ((l & 128) || (this.noAssert && typeof l === "undefined")) {
                    l = this.view[r++];
                    q |= (l & 127) << 14;
                    if ((l & 128) || (this.noAssert && typeof l === "undefined")) {
                        l = this.view[r++];
                        q |= (l & 127) << 21;
                        if ((l & 128) || (this.noAssert && typeof l === "undefined")) {
                            l = this.view[r++];
                            p = (l & 127);
                            if ((l & 128) || (this.noAssert && typeof l === "undefined")) {
                                l = this.view[r++];
                                p |= (l & 127) << 7;
                                if ((l & 128) || (this.noAssert && typeof l === "undefined")) {
                                    l = this.view[r++];
                                    p |= (l & 127) << 14;
                                    if ((l & 128) || (this.noAssert && typeof l === "undefined")) {
                                        l = this.view[r++];
                                        p |= (l & 127) << 21;
                                        if ((l & 128) || (this.noAssert && typeof l === "undefined")) {
                                            l = this.view[r++];
                                            n = (l & 127);
                                            if ((l & 128) || (this.noAssert && typeof l === "undefined")) {
                                                l = this.view[r++];
                                                n |= (l & 127) << 7;
                                                if ((l & 128) || (this.noAssert && typeof l === "undefined")) {
                                                    throw Error("Buffer overrun")
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            var m = f.fromBits(q | (p << 28), (p >>> 4) | (n) << 24, false);
            if (o) {
                this.offset = r;
                return m
            } else {
                return {
                    value: m,
                    length: r - s
                }
            }
        }
        ;
        g.readVarint64ZigZag = function(m) {
            var l = this.readVarint64(m);
            if (l && l.value instanceof f) {
                l.value = i.zigZagDecode64(l.value)
            } else {
                l = i.zigZagDecode64(l)
            }
            return l
        }
    }
    g.writeCString = function(q, p) {
        var o = typeof p === "undefined";
        if (o) {
            p = this.offset
        }
        var m, l = q.length;
        if (!this.noAssert) {
            if (typeof q !== "string") {
                throw TypeError("Illegal str: Not a string")
            }
            for (m = 0; m < l; ++m) {
                if (q.charCodeAt(m) === 0) {
                    throw RangeError("Illegal str: Contains NULL-characters")
                }
            }
            if (typeof p !== "number" || p % 1 !== 0) {
                throw TypeError("Illegal offset: " + p + " (not an integer)")
            }
            p >>>= 0;
            if (p < 0 || p + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + p + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        l = j.calculateUTF16asUTF8(a(q))[1];
        p += l + 1;
        var n = this.buffer.byteLength;
        if (p > n) {
            this.resize((n *= 2) > p ? n : p)
        }
        p -= l + 1;
        j.encodeUTF16toUTF8(a(q), function(r) {
            this.view[p++] = r
        }
        .bind(this));
        this.view[p++] = 0;
        if (o) {
            this.offset = p;
            return this
        }
        return l
    }
    ;
    g.readCString = function(p) {
        var n = typeof p === "undefined";
        if (n) {
            p = this.offset
        }
        if (!this.noAssert) {
            if (typeof p !== "number" || p % 1 !== 0) {
                throw TypeError("Illegal offset: " + p + " (not an integer)")
            }
            p >>>= 0;
            if (p < 0 || p + 1 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + p + " (+" + 1 + ") <= " + this.buffer.byteLength)
            }
        }
        var q = p, m;
        var o, l = -1;
        j.decodeUTF8toUTF16(function() {
            if (l === 0) {
                return null
            }
            if (p >= this.limit) {
                throw RangeError("Illegal range: Truncated data, " + p + " < " + this.limit)
            }
            l = this.view[p++];
            return l === 0 ? null : l
        }
        .bind(this), o = b(), true);
        if (n) {
            this.offset = p;
            return o()
        } else {
            return {
                string: o(),
                length: p - q
            }
        }
    }
    ;
    g.writeIString = function(p, o) {
        var n = typeof o === "undefined";
        if (n) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof p !== "string") {
                throw TypeError("Illegal str: Not a string")
            }
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        var q = o, l;
        l = j.calculateUTF16asUTF8(a(p), this.noAssert)[1];
        o += 4 + l;
        var m = this.buffer.byteLength;
        if (o > m) {
            this.resize((m *= 2) > o ? m : o)
        }
        o -= 4 + l;
        if (this.littleEndian) {
            this.view[o + 3] = (l >>> 24) & 255;
            this.view[o + 2] = (l >>> 16) & 255;
            this.view[o + 1] = (l >>> 8) & 255;
            this.view[o] = l & 255
        } else {
            this.view[o] = (l >>> 24) & 255;
            this.view[o + 1] = (l >>> 16) & 255;
            this.view[o + 2] = (l >>> 8) & 255;
            this.view[o + 3] = l & 255
        }
        o += 4;
        j.encodeUTF16toUTF8(a(p), function(r) {
            this.view[o++] = r
        }
        .bind(this));
        if (o !== q + 4 + l) {
            throw RangeError("Illegal range: Truncated data, " + o + " == " + (o + 4 + l))
        }
        if (n) {
            this.offset = o;
            return this
        }
        return o - q
    }
    ;
    g.readIString = function(o) {
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 4 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 4 + ") <= " + this.buffer.byteLength)
            }
        }
        var p = o;
        var l = this.readUint32(o);
        var n = this.readUTF8String(l, i.METRICS_BYTES, o += 4);
        o += n.length;
        if (m) {
            this.offset = o;
            return n.string
        } else {
            return {
                string: n.string,
                length: o - p
            }
        }
    }
    ;
    i.METRICS_CHARS = "c";
    i.METRICS_BYTES = "b";
    g.writeUTF8String = function(p, o) {
        var n = typeof o === "undefined";
        if (n) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        var l;
        var q = o;
        l = j.calculateUTF16asUTF8(a(p))[1];
        o += l;
        var m = this.buffer.byteLength;
        if (o > m) {
            this.resize((m *= 2) > o ? m : o)
        }
        o -= l;
        j.encodeUTF16toUTF8(a(p), function(r) {
            this.view[o++] = r
        }
        .bind(this));
        if (n) {
            this.offset = o;
            return this
        }
        return o - q
    }
    ;
    g.writeString = g.writeUTF8String;
    i.calculateUTF8Chars = function(l) {
        return j.calculateUTF16asUTF8(a(l))[0]
    }
    ;
    i.calculateUTF8Bytes = function(l) {
        return j.calculateUTF16asUTF8(a(l))[1]
    }
    ;
    i.calculateString = i.calculateUTF8Bytes;
    g.readUTF8String = function(o, n, r) {
        if (typeof n === "number") {
            r = n;
            n = undefined
        }
        var p = typeof r === "undefined";
        if (p) {
            r = this.offset
        }
        if (typeof n === "undefined") {
            n = i.METRICS_CHARS
        }
        if (!this.noAssert) {
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal length: " + o + " (not an integer)")
            }
            o |= 0;
            if (typeof r !== "number" || r % 1 !== 0) {
                throw TypeError("Illegal offset: " + r + " (not an integer)")
            }
            r >>>= 0;
            if (r < 0 || r + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + r + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        var m = 0, s = r, q;
        if (n === i.METRICS_CHARS) {
            q = b();
            j.decodeUTF8(function() {
                return m < o && r < this.limit ? this.view[r++] : null
            }
            .bind(this), function(t) {
                ++m;
                j.UTF8toUTF16(t, q)
            });
            if (m !== o) {
                throw RangeError("Illegal range: Truncated data, " + m + " == " + o)
            }
            if (p) {
                this.offset = r;
                return q()
            } else {
                return {
                    string: q(),
                    length: r - s
                }
            }
        } else {
            if (n === i.METRICS_BYTES) {
                if (!this.noAssert) {
                    if (typeof r !== "number" || r % 1 !== 0) {
                        throw TypeError("Illegal offset: " + r + " (not an integer)")
                    }
                    r >>>= 0;
                    if (r < 0 || r + o > this.buffer.byteLength) {
                        throw RangeError("Illegal offset: 0 <= " + r + " (+" + o + ") <= " + this.buffer.byteLength)
                    }
                }
                var l = r + o;
                j.decodeUTF8toUTF16(function() {
                    return r < l ? this.view[r++] : null
                }
                .bind(this), q = b(), this.noAssert);
                if (r !== l) {
                    throw RangeError("Illegal range: Truncated data, " + r + " == " + l)
                }
                if (p) {
                    this.offset = r;
                    return q()
                } else {
                    return {
                        string: q(),
                        length: r - s
                    }
                }
            } else {
                throw TypeError("Unsupported metrics: " + n)
            }
        }
    }
    ;
    g.readString = g.readUTF8String;
    g.writeVString = function(r, q) {
        var p = typeof q === "undefined";
        if (p) {
            q = this.offset
        }
        if (!this.noAssert) {
            if (typeof r !== "string") {
                throw TypeError("Illegal str: Not a string")
            }
            if (typeof q !== "number" || q % 1 !== 0) {
                throw TypeError("Illegal offset: " + q + " (not an integer)")
            }
            q >>>= 0;
            if (q < 0 || q + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + q + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        var s = q, o, m;
        o = j.calculateUTF16asUTF8(a(r), this.noAssert)[1];
        m = i.calculateVarint32(o);
        q += m + o;
        var n = this.buffer.byteLength;
        if (q > n) {
            this.resize((n *= 2) > q ? n : q)
        }
        q -= m + o;
        q += this.writeVarint32(o, q);
        j.encodeUTF16toUTF8(a(r), function(l) {
            this.view[q++] = l
        }
        .bind(this));
        if (q !== s + o + m) {
            throw RangeError("Illegal range: Truncated data, " + q + " == " + (q + o + m))
        }
        if (p) {
            this.offset = q;
            return this
        }
        return q - s
    }
    ;
    g.readVString = function(o) {
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 1 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 1 + ") <= " + this.buffer.byteLength)
            }
        }
        var p = o;
        var l = this.readVarint32(o);
        var n = this.readUTF8String(l.value, i.METRICS_BYTES, o += l.length);
        o += n.length;
        if (m) {
            this.offset = o;
            return n.string
        } else {
            return {
                string: n.string,
                length: o - p
            }
        }
    }
    ;
    g.append = function(p, n, q) {
        if (typeof n === "number" || typeof n !== "string") {
            q = n;
            n = undefined
        }
        var o = typeof q === "undefined";
        if (o) {
            q = this.offset
        }
        if (!this.noAssert) {
            if (typeof q !== "number" || q % 1 !== 0) {
                throw TypeError("Illegal offset: " + q + " (not an integer)")
            }
            q >>>= 0;
            if (q < 0 || q + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + q + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        if (!(p instanceof i)) {
            p = i.wrap(p, n)
        }
        var m = p.limit - p.offset;
        if (m <= 0) {
            return this
        }
        q += m;
        var l = this.buffer.byteLength;
        if (q > l) {
            this.resize((l *= 2) > q ? l : q)
        }
        q -= m;
        this.view.set(p.view.subarray(p.offset, p.limit), q);
        p.offset += m;
        if (o) {
            this.offset += m
        }
        return this
    }
    ;
    g.appendTo = function(l, m) {
        l.append(this, m);
        return this
    }
    ;
    g.assert = function(l) {
        this.noAssert = !l;
        return this
    }
    ;
    g.capacity = function() {
        return this.buffer.byteLength
    }
    ;
    g.clear = function() {
        this.offset = 0;
        this.limit = this.buffer.byteLength;
        this.markedOffset = -1;
        return this
    }
    ;
    g.clone = function(m) {
        var l = new i(0,this.littleEndian,this.noAssert);
        if (m) {
            l.buffer = new ArrayBuffer(this.buffer.byteLength);
            l.view = new Uint8Array(l.buffer)
        } else {
            l.buffer = this.buffer;
            l.view = this.view
        }
        l.offset = this.offset;
        l.markedOffset = this.markedOffset;
        l.limit = this.limit;
        return l
    }
    ;
    g.compact = function(p, o) {
        if (typeof p === "undefined") {
            p = this.offset
        }
        if (typeof o === "undefined") {
            o = this.limit
        }
        if (!this.noAssert) {
            if (typeof p !== "number" || p % 1 !== 0) {
                throw TypeError("Illegal begin: Not an integer")
            }
            p >>>= 0;
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal end: Not an integer")
            }
            o >>>= 0;
            if (p < 0 || p > o || o > this.buffer.byteLength) {
                throw RangeError("Illegal range: 0 <= " + p + " <= " + o + " <= " + this.buffer.byteLength)
            }
        }
        if (p === 0 && o === this.buffer.byteLength) {
            return this
        }
        var l = o - p;
        if (l === 0) {
            this.buffer = k;
            this.view = null;
            if (this.markedOffset >= 0) {
                this.markedOffset -= p
            }
            this.offset = 0;
            this.limit = 0;
            return this
        }
        var n = new ArrayBuffer(l);
        var m = new Uint8Array(n);
        m.set(this.view.subarray(p, o));
        this.buffer = n;
        this.view = m;
        if (this.markedOffset >= 0) {
            this.markedOffset -= p
        }
        this.offset = 0;
        this.limit = l;
        return this
    }
    ;
    g.copy = function(n, l) {
        if (typeof n === "undefined") {
            n = this.offset
        }
        if (typeof l === "undefined") {
            l = this.limit
        }
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal begin: Not an integer")
            }
            n >>>= 0;
            if (typeof l !== "number" || l % 1 !== 0) {
                throw TypeError("Illegal end: Not an integer")
            }
            l >>>= 0;
            if (n < 0 || n > l || l > this.buffer.byteLength) {
                throw RangeError("Illegal range: 0 <= " + n + " <= " + l + " <= " + this.buffer.byteLength)
            }
        }
        if (n === l) {
            return new i(0,this.littleEndian,this.noAssert)
        }
        var m = l - n
          , o = new i(m,this.littleEndian,this.noAssert);
        o.offset = 0;
        o.limit = m;
        if (o.markedOffset >= 0) {
            o.markedOffset -= n
        }
        this.copyTo(o, 0, n, l);
        return o
    }
    ;
    g.copyTo = function(p, r, n, q) {
        var o, m;
        if (!this.noAssert) {
            if (!i.isByteBuffer(p)) {
                throw TypeError("Illegal target: Not a ByteBuffer")
            }
        }
        r = (m = typeof r === "undefined") ? p.offset : r | 0;
        n = (o = typeof n === "undefined") ? this.offset : n | 0;
        q = typeof q === "undefined" ? this.limit : q | 0;
        if (r < 0 || r > p.buffer.byteLength) {
            throw RangeError("Illegal target range: 0 <= " + r + " <= " + p.buffer.byteLength)
        }
        if (n < 0 || q > this.buffer.byteLength) {
            throw RangeError("Illegal source range: 0 <= " + n + " <= " + this.buffer.byteLength)
        }
        var l = q - n;
        if (l === 0) {
            return p
        }
        p.ensureCapacity(r + l);
        p.view.set(this.view.subarray(n, q), r);
        if (o) {
            this.offset += l
        }
        if (m) {
            p.offset += l
        }
        return this
    }
    ;
    g.ensureCapacity = function(l) {
        var m = this.buffer.byteLength;
        if (m < l) {
            return this.resize((m *= 2) > l ? m : l)
        }
        return this
    }
    ;
    g.fill = function(o, m, l) {
        var n = typeof m === "undefined";
        if (n) {
            m = this.offset
        }
        if (typeof o === "string" && o.length > 0) {
            o = o.charCodeAt(0)
        }
        if (typeof m === "undefined") {
            m = this.offset
        }
        if (typeof l === "undefined") {
            l = this.limit
        }
        if (!this.noAssert) {
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal value: " + o + " (not an integer)")
            }
            o |= 0;
            if (typeof m !== "number" || m % 1 !== 0) {
                throw TypeError("Illegal begin: Not an integer")
            }
            m >>>= 0;
            if (typeof l !== "number" || l % 1 !== 0) {
                throw TypeError("Illegal end: Not an integer")
            }
            l >>>= 0;
            if (m < 0 || m > l || l > this.buffer.byteLength) {
                throw RangeError("Illegal range: 0 <= " + m + " <= " + l + " <= " + this.buffer.byteLength)
            }
        }
        if (m >= l) {
            return this
        }
        while (m < l) {
            this.view[m++] = o
        }
        if (n) {
            this.offset = m
        }
        return this
    }
    ;
    g.flip = function() {
        this.limit = this.offset;
        this.offset = 0;
        return this
    }
    ;
    g.mark = function(l) {
        l = typeof l === "undefined" ? this.offset : l;
        if (!this.noAssert) {
            if (typeof l !== "number" || l % 1 !== 0) {
                throw TypeError("Illegal offset: " + l + " (not an integer)")
            }
            l >>>= 0;
            if (l < 0 || l + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + l + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        this.markedOffset = l;
        return this
    }
    ;
    g.order = function(l) {
        if (!this.noAssert) {
            if (typeof l !== "boolean") {
                throw TypeError("Illegal littleEndian: Not a boolean")
            }
        }
        this.littleEndian = !!l;
        return this
    }
    ;
    g.LE = function(l) {
        this.littleEndian = typeof l !== "undefined" ? !!l : true;
        return this
    }
    ;
    g.BE = function(l) {
        this.littleEndian = typeof l !== "undefined" ? !l : false;
        return this
    }
    ;
    g.prepend = function(l, n, o) {
        if (typeof n === "number" || typeof n !== "string") {
            o = n;
            n = undefined
        }
        var m = typeof o === "undefined";
        if (m) {
            o = this.offset
        }
        if (!this.noAssert) {
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: " + o + " (not an integer)")
            }
            o >>>= 0;
            if (o < 0 || o + 0 > this.buffer.byteLength) {
                throw RangeError("Illegal offset: 0 <= " + o + " (+" + 0 + ") <= " + this.buffer.byteLength)
            }
        }
        if (!(l instanceof i)) {
            l = i.wrap(l, n)
        }
        var q = l.limit - l.offset;
        if (q <= 0) {
            return this
        }
        var t = q - o;
        if (t > 0) {
            var p = new ArrayBuffer(this.buffer.byteLength + t);
            var s = new Uint8Array(p);
            s.set(this.view.subarray(o, this.buffer.byteLength), q);
            this.buffer = p;
            this.view = s;
            this.offset += t;
            if (this.markedOffset >= 0) {
                this.markedOffset += t
            }
            this.limit += t;
            o += t
        } else {
            var r = new Uint8Array(this.buffer)
        }
        this.view.set(l.view.subarray(l.offset, l.limit), o - q);
        l.offset = l.limit;
        if (m) {
            this.offset -= q
        }
        return this
    }
    ;
    g.prependTo = function(l, m) {
        l.prepend(this, m);
        return this
    }
    ;
    g.printDebug = function(l) {
        if (typeof l !== "function") {
            l = console.log.bind(console)
        }
        l(this.toString() + "\n-------------------------------------------------------------------\n" + this.toDebug(true))
    }
    ;
    g.remaining = function() {
        return this.limit - this.offset
    }
    ;
    g.reset = function() {
        if (this.markedOffset >= 0) {
            this.offset = this.markedOffset;
            this.markedOffset = -1
        } else {
            this.offset = 0
        }
        return this
    }
    ;
    g.resize = function(n) {
        if (!this.noAssert) {
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal capacity: " + n + " (not an integer)")
            }
            n |= 0;
            if (n < 0) {
                throw RangeError("Illegal capacity: 0 <= " + n)
            }
        }
        if (this.buffer.byteLength < n) {
            var m = new ArrayBuffer(n);
            var l = new Uint8Array(m);
            l.set(this.view);
            this.buffer = m;
            this.view = l
        }
        return this
    }
    ;
    g.reverse = function(m, l) {
        if (typeof m === "undefined") {
            m = this.offset
        }
        if (typeof l === "undefined") {
            l = this.limit
        }
        if (!this.noAssert) {
            if (typeof m !== "number" || m % 1 !== 0) {
                throw TypeError("Illegal begin: Not an integer")
            }
            m >>>= 0;
            if (typeof l !== "number" || l % 1 !== 0) {
                throw TypeError("Illegal end: Not an integer")
            }
            l >>>= 0;
            if (m < 0 || m > l || l > this.buffer.byteLength) {
                throw RangeError("Illegal range: 0 <= " + m + " <= " + l + " <= " + this.buffer.byteLength)
            }
        }
        if (m === l) {
            return this
        }
        Array.prototype.reverse.call(this.view.subarray(m, l));
        return this
    }
    ;
    g.skip = function(l) {
        if (!this.noAssert) {
            if (typeof l !== "number" || l % 1 !== 0) {
                throw TypeError("Illegal length: " + l + " (not an integer)")
            }
            l |= 0
        }
        var m = this.offset + l;
        if (!this.noAssert) {
            if (m < 0 || m > this.buffer.byteLength) {
                throw RangeError("Illegal length: 0 <= " + this.offset + " + " + l + " <= " + this.buffer.byteLength)
            }
        }
        this.offset = m;
        return this
    }
    ;
    g.slice = function(m, l) {
        if (typeof m === "undefined") {
            m = this.offset
        }
        if (typeof l === "undefined") {
            l = this.limit
        }
        if (!this.noAssert) {
            if (typeof m !== "number" || m % 1 !== 0) {
                throw TypeError("Illegal begin: Not an integer")
            }
            m >>>= 0;
            if (typeof l !== "number" || l % 1 !== 0) {
                throw TypeError("Illegal end: Not an integer")
            }
            l >>>= 0;
            if (m < 0 || m > l || l > this.buffer.byteLength) {
                throw RangeError("Illegal range: 0 <= " + m + " <= " + l + " <= " + this.buffer.byteLength)
            }
        }
        var n = this.clone();
        n.offset = m;
        n.limit = l;
        return n
    }
    ;
    g.toBuffer = function(l) {
        var o = this.offset
          , n = this.limit;
        if (!this.noAssert) {
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal offset: Not an integer")
            }
            o >>>= 0;
            if (typeof n !== "number" || n % 1 !== 0) {
                throw TypeError("Illegal limit: Not an integer")
            }
            n >>>= 0;
            if (o < 0 || o > n || n > this.buffer.byteLength) {
                throw RangeError("Illegal range: 0 <= " + o + " <= " + n + " <= " + this.buffer.byteLength)
            }
        }
        if (!l && o === 0 && n === this.buffer.byteLength) {
            return this.buffer
        }
        if (o === n) {
            return k
        }
        var m = new ArrayBuffer(n - o);
        new Uint8Array(m).set(new Uint8Array(this.buffer).subarray(o, n), 0);
        return m
    }
    ;
    g.toArrayBuffer = g.toBuffer;
    g.toString = function(n, m, l) {
        if (typeof n === "undefined") {
            return "ByteBufferAB(offset=" + this.offset + ",markedOffset=" + this.markedOffset + ",limit=" + this.limit + ",capacity=" + this.capacity() + ")"
        }
        if (typeof n === "number") {
            n = "utf8",
            m = n,
            l = m
        }
        switch (n) {
        case "utf8":
            return this.toUTF8(m, l);
        case "base64":
            return this.toBase64(m, l);
        case "hex":
            return this.toHex(m, l);
        case "binary":
            return this.toBinary(m, l);
        case "debug":
            return this.toDebug();
        case "columns":
            return this.toColumns();
        default:
            throw Error("Unsupported encoding: " + n)
        }
    }
    ;
    var c = function() {
        var m = {};
        var p = [65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 43, 47];
        var o = [];
        for (var n = 0, l = p.length; n < l; ++n) {
            o[p[n]] = n
        }
        m.encode = function(s, u) {
            var q, r;
            while ((q = s()) !== null) {
                u(p[(q >> 2) & 63]);
                r = (q & 3) << 4;
                if ((q = s()) !== null) {
                    r |= (q >> 4) & 15;
                    u(p[(r | ((q >> 4) & 15)) & 63]);
                    r = (q & 15) << 2;
                    if ((q = s()) !== null) {
                        u(p[(r | ((q >> 6) & 3)) & 63]),
                        u(p[q & 63])
                    } else {
                        u(p[r & 63]),
                        u(61)
                    }
                } else {
                    u(p[r & 63]),
                    u(61),
                    u(61)
                }
            }
        }
        ;
        m.decode = function(t, v) {
            var u, s, r;
            function q(w) {
                throw Error("Illegal character code: " + w)
            }
            while ((u = t()) !== null) {
                s = o[u];
                if (typeof s === "undefined") {
                    q(u)
                }
                if ((u = t()) !== null) {
                    r = o[u];
                    if (typeof r === "undefined") {
                        q(u)
                    }
                    v((s << 2) >>> 0 | (r & 48) >> 4);
                    if ((u = t()) !== null) {
                        s = o[u];
                        if (typeof s === "undefined") {
                            if (u === 61) {
                                break
                            } else {
                                q(u)
                            }
                        }
                        v(((r & 15) << 4) >>> 0 | (s & 60) >> 2);
                        if ((u = t()) !== null) {
                            r = o[u];
                            if (typeof r === "undefined") {
                                if (u === 61) {
                                    break
                                } else {
                                    q(u)
                                }
                            }
                            v(((s & 3) << 6) >>> 0 | r)
                        }
                    }
                }
            }
        }
        ;
        m.test = function(q) {
            return /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(q)
        }
        ;
        return m
    }();
    g.toBase64 = function(m, l) {
        if (typeof m === "undefined") {
            m = this.offset
        }
        if (typeof l === "undefined") {
            l = this.limit
        }
        m = m | 0;
        l = l | 0;
        if (m < 0 || l > this.capacity || m > l) {
            throw RangeError("begin, end")
        }
        var n;
        c.encode(function() {
            return m < l ? this.view[m++] : null
        }
        .bind(this), n = b());
        return n()
    }
    ;
    i.fromBase64 = function(o, m) {
        if (typeof o !== "string") {
            throw TypeError("str")
        }
        var n = new i(o.length / 4 * 3,m)
          , l = 0;
        c.decode(a(o), function(p) {
            n.view[l++] = p
        });
        n.limit = l;
        return n
    }
    ;
    i.btoa = function(l) {
        return i.fromBinary(l).toBase64()
    }
    ;
    i.atob = function(l) {
        return i.fromBase64(l).toBinary()
    }
    ;
    g.toBinary = function(m, l) {
        if (typeof m === "undefined") {
            m = this.offset
        }
        if (typeof l === "undefined") {
            l = this.limit
        }
        m |= 0;
        l |= 0;
        if (m < 0 || l > this.capacity() || m > l) {
            throw RangeError("begin, end")
        }
        if (m === l) {
            return ""
        }
        var n = []
          , o = [];
        while (m < l) {
            n.push(this.view[m++]);
            if (n.length >= 1024) {
                o.push(String.fromCharCode.apply(String, n)),
                n = []
            }
        }
        return o.join("") + String.fromCharCode.apply(String, n)
    }
    ;
    i.fromBinary = function(q, o) {
        if (typeof q !== "string") {
            throw TypeError("str")
        }
        var n = 0, m = q.length, l, p = new i(m,o);
        while (n < m) {
            l = q.charCodeAt(n);
            if (l > 255) {
                throw RangeError("illegal char code: " + l)
            }
            p.view[n++] = l
        }
        p.limit = m;
        return p
    }
    ;
    g.toDebug = function(p) {
        var o = -1, m = this.buffer.byteLength, l, r = "", q = "", n = "";
        while (o < m) {
            if (o !== -1) {
                l = this.view[o];
                if (l < 16) {
                    r += "0" + l.toString(16).toUpperCase()
                } else {
                    r += l.toString(16).toUpperCase()
                }
                if (p) {
                    q += l > 32 && l < 127 ? String.fromCharCode(l) : "."
                }
            }
            ++o;
            if (p) {
                if (o > 0 && o % 16 === 0 && o !== m) {
                    while (r.length < 3 * 16 + 3) {
                        r += " "
                    }
                    n += r + q + "\n";
                    r = q = ""
                }
            }
            if (o === this.offset && o === this.limit) {
                r += o === this.markedOffset ? "!" : "|"
            } else {
                if (o === this.offset) {
                    r += o === this.markedOffset ? "[" : "<"
                } else {
                    if (o === this.limit) {
                        r += o === this.markedOffset ? "]" : ">"
                    } else {
                        r += o === this.markedOffset ? "'" : (p || (o !== 0 && o !== m) ? " " : "")
                    }
                }
            }
        }
        if (p && r !== " ") {
            while (r.length < 3 * 16 + 3) {
                r += " "
            }
            n += r + q + "\n"
        }
        return p ? n : r
    }
    ;
    i.fromDebug = function(v, n, x) {
        var r = v.length
          , u = new i(((r + 1) / 3) | 0,n,x);
        var t = 0, s = 0, l, w, q = false, y = false, m = false, o = false, p = false;
        while (t < r) {
            switch (l = v.charAt(t++)) {
            case "!":
                if (!x) {
                    if (y || m || o) {
                        p = true;
                        break
                    }
                    y = m = o = true
                }
                u.offset = u.markedOffset = u.limit = s;
                q = false;
                break;
            case "|":
                if (!x) {
                    if (y || o) {
                        p = true;
                        break
                    }
                    y = o = true
                }
                u.offset = u.limit = s;
                q = false;
                break;
            case "[":
                if (!x) {
                    if (y || m) {
                        p = true;
                        break
                    }
                    y = m = true
                }
                u.offset = u.markedOffset = s;
                q = false;
                break;
            case "<":
                if (!x) {
                    if (y) {
                        p = true;
                        break
                    }
                    y = true
                }
                u.offset = s;
                q = false;
                break;
            case "]":
                if (!x) {
                    if (o || m) {
                        p = true;
                        break
                    }
                    o = m = true
                }
                u.limit = u.markedOffset = s;
                q = false;
                break;
            case ">":
                if (!x) {
                    if (o) {
                        p = true;
                        break
                    }
                    o = true
                }
                u.limit = s;
                q = false;
                break;
            case "'":
                if (!x) {
                    if (m) {
                        p = true;
                        break
                    }
                    m = true
                }
                u.markedOffset = s;
                q = false;
                break;
            case " ":
                q = false;
                break;
            default:
                if (!x) {
                    if (q) {
                        p = true;
                        break
                    }
                }
                w = parseInt(l + v.charAt(t++), 16);
                if (!x) {
                    if (isNaN(w) || w < 0 || w > 255) {
                        throw TypeError("Illegal str: Not a debug encoded string")
                    }
                }
                u.view[s++] = w;
                q = true
            }
            if (p) {
                throw TypeError("Illegal str: Invalid symbol at " + t)
            }
        }
        if (!x) {
            if (!y || !o) {
                throw TypeError("Illegal str: Missing offset or limit")
            }
            if (s < u.buffer.byteLength) {
                throw TypeError("Illegal str: Not a debug encoded string (is it hex?) " + s + " < " + r)
            }
        }
        return u
    }
    ;
    g.toHex = function(o, m) {
        o = typeof o === "undefined" ? this.offset : o;
        m = typeof m === "undefined" ? this.limit : m;
        if (!this.noAssert) {
            if (typeof o !== "number" || o % 1 !== 0) {
                throw TypeError("Illegal begin: Not an integer")
            }
            o >>>= 0;
            if (typeof m !== "number" || m % 1 !== 0) {
                throw TypeError("Illegal end: Not an integer")
            }
            m >>>= 0;
            if (o < 0 || o > m || m > this.buffer.byteLength) {
                throw RangeError("Illegal range: 0 <= " + o + " <= " + m + " <= " + this.buffer.byteLength)
            }
        }
        var n = new Array(m - o), l;
        while (o < m) {
            l = this.view[o++];
            if (l < 16) {
                n.push("0", l.toString(16))
            } else {
                n.push(l.toString(16))
            }
        }
        return n.join("")
    }
    ;
    i.fromHex = function(s, q, p) {
        if (!p) {
            if (typeof s !== "string") {
                throw TypeError("Illegal str: Not a string")
            }
            if (s.length % 2 !== 0) {
                throw TypeError("Illegal str: Length not a multiple of 2")
            }
        }
        var m = s.length, r = new i((m / 2) | 0,q), l;
        for (var o = 0, n = 0; o < m; o += 2) {
            l = parseInt(s.substring(o, o + 2), 16);
            if (!p) {
                if (!isFinite(l) || l < 0 || l > 255) {
                    throw TypeError("Illegal str: Contains non-hex characters")
                }
            }
            r.view[n++] = l
        }
        r.limit = n;
        return r
    }
    ;
    var j = function() {
        var l = {};
        l.MAX_CODEPOINT = 1114111;
        l.encodeUTF8 = function(n, o) {
            var m = null;
            if (typeof n === "number") {
                m = n,
                n = function() {
                    return null
                }
            }
            while (m !== null || (m = n()) !== null) {
                if (m < 128) {
                    o(m & 127)
                } else {
                    if (m < 2048) {
                        o(((m >> 6) & 31) | 192),
                        o((m & 63) | 128)
                    } else {
                        if (m < 65536) {
                            o(((m >> 12) & 15) | 224),
                            o(((m >> 6) & 63) | 128),
                            o((m & 63) | 128)
                        } else {
                            o(((m >> 18) & 7) | 240),
                            o(((m >> 12) & 63) | 128),
                            o(((m >> 6) & 63) | 128),
                            o((m & 63) | 128)
                        }
                    }
                }
                m = null
            }
        }
        ;
        l.decodeUTF8 = function(q, s) {
            var o, m, r, p, n = function(t) {
                t = t.slice(0, t.indexOf(null));
                var u = Error(t.toString());
                u.name = "TruncatedError";
                u.bytes = t;
                throw u
            };
            while ((o = q()) !== null) {
                if ((o & 128) === 0) {
                    s(o)
                } else {
                    if ((o & 224) === 192) {
                        ((m = q()) === null) && n([o, m]),
                        s(((o & 31) << 6) | (m & 63))
                    } else {
                        if ((o & 240) === 224) {
                            ((m = q()) === null || (r = q()) === null) && n([o, m, r]),
                            s(((o & 15) << 12) | ((m & 63) << 6) | (r & 63))
                        } else {
                            if ((o & 248) === 240) {
                                ((m = q()) === null || (r = q()) === null || (p = q()) === null) && n([o, m, r, p]),
                                s(((o & 7) << 18) | ((m & 63) << 12) | ((r & 63) << 6) | (p & 63))
                            } else {
                                throw RangeError("Illegal starting byte: " + o)
                            }
                        }
                    }
                }
            }
        }
        ;
        l.UTF16toUTF8 = function(o, p) {
            var n, m = null;
            while (true) {
                if ((n = m !== null ? m : o()) === null) {
                    break
                }
                if (n >= 55296 && n <= 57343) {
                    if ((m = o()) !== null) {
                        if (m >= 56320 && m <= 57343) {
                            p((n - 55296) * 1024 + m - 56320 + 65536);
                            m = null;
                            continue
                        }
                    }
                }
                p(n)
            }
            if (m !== null) {
                p(m)
            }
        }
        ;
        l.UTF8toUTF16 = function(n, o) {
            var m = null;
            if (typeof n === "number") {
                m = n,
                n = function() {
                    return null
                }
            }
            while (m !== null || (m = n()) !== null) {
                if (m <= 65535) {
                    o(m)
                } else {
                    m -= 65536,
                    o((m >> 10) + 55296),
                    o((m % 1024) + 56320)
                }
                m = null
            }
        }
        ;
        l.encodeUTF16toUTF8 = function(m, n) {
            l.UTF16toUTF8(m, function(o) {
                l.encodeUTF8(o, n)
            })
        }
        ;
        l.decodeUTF8toUTF16 = function(m, n) {
            l.decodeUTF8(m, function(o) {
                l.UTF8toUTF16(o, n)
            })
        }
        ;
        l.calculateCodePoint = function(m) {
            return (m < 128) ? 1 : (m < 2048) ? 2 : (m < 65536) ? 3 : 4
        }
        ;
        l.calculateUTF8 = function(o) {
            var n, m = 0;
            while ((n = o()) !== null) {
                m += (n < 128) ? 1 : (n < 2048) ? 2 : (n < 65536) ? 3 : 4
            }
            return m
        }
        ;
        l.calculateUTF16asUTF8 = function(o) {
            var p = 0
              , m = 0;
            l.UTF16toUTF8(o, function(n) {
                ++p;
                m += (n < 128) ? 1 : (n < 2048) ? 2 : (n < 65536) ? 3 : 4
            });
            return [p, m]
        }
        ;
        return l
    }();
    g.toUTF8 = function(m, l) {
        if (typeof m === "undefined") {
            m = this.offset
        }
        if (typeof l === "undefined") {
            l = this.limit
        }
        if (!this.noAssert) {
            if (typeof m !== "number" || m % 1 !== 0) {
                throw TypeError("Illegal begin: Not an integer")
            }
            m >>>= 0;
            if (typeof l !== "number" || l % 1 !== 0) {
                throw TypeError("Illegal end: Not an integer")
            }
            l >>>= 0;
            if (m < 0 || m > l || l > this.buffer.byteLength) {
                throw RangeError("Illegal range: 0 <= " + m + " <= " + l + " <= " + this.buffer.byteLength)
            }
        }
        var o;
        try {
            j.decodeUTF8toUTF16(function() {
                return m < l ? this.view[m++] : null
            }
            .bind(this), o = b())
        } catch (n) {
            if (m !== l) {
                throw RangeError("Illegal range: Truncated data, " + m + " != " + l)
            }
        }
        return o()
    }
    ;
    i.fromUTF8 = function(p, n, m) {
        if (!m) {
            if (typeof p !== "string") {
                throw TypeError("Illegal str: Not a string")
            }
        }
        var o = new i(j.calculateUTF16asUTF8(a(p), true)[1],n,m)
          , l = 0;
        j.encodeUTF16toUTF8(a(p), function(q) {
            o.view[l++] = q
        });
        o.limit = l;
        return o
    }
    ;
    return i
});
(function(b, a) {
    if (typeof define === "function" && define.amd) {
        define(["/v2/web/boss/js/module/chat-bytebuffer.js"], function() {
            (b.dcodeIO = b.dcodeIO || {})["ProtoBuf"] = a(b.dcodeIO["ByteBuffer"])
        })
    } else {
        if (typeof require === "function" && typeof module === "object" && module && module.exports) {
            module.exports = a(require("bytebuffer"), true)
        } else {
            (b.dcodeIO = b.dcodeIO || {})["ProtoBuf"] = a(b.dcodeIO["ByteBuffer"])
        }
    }
}
)(this, function(b, a) {
    var c = {};
    c.ByteBuffer = b;
    c.Long = b.Long || null;
    c.VERSION = "5.0.1";
    c.WIRE_TYPES = {};
    c.WIRE_TYPES.VARINT = 0;
    c.WIRE_TYPES.BITS64 = 1;
    c.WIRE_TYPES.LDELIM = 2;
    c.WIRE_TYPES.STARTGROUP = 3;
    c.WIRE_TYPES.ENDGROUP = 4;
    c.WIRE_TYPES.BITS32 = 5;
    c.PACKABLE_WIRE_TYPES = [c.WIRE_TYPES.VARINT, c.WIRE_TYPES.BITS64, c.WIRE_TYPES.BITS32];
    c.TYPES = {
        int32: {
            name: "int32",
            wireType: c.WIRE_TYPES.VARINT,
            defaultValue: 0
        },
        uint32: {
            name: "uint32",
            wireType: c.WIRE_TYPES.VARINT,
            defaultValue: 0
        },
        sint32: {
            name: "sint32",
            wireType: c.WIRE_TYPES.VARINT,
            defaultValue: 0
        },
        int64: {
            name: "int64",
            wireType: c.WIRE_TYPES.VARINT,
            defaultValue: 0
        },
        uint64: {
            name: "uint64",
            wireType: c.WIRE_TYPES.VARINT,
            defaultValue: c.Long ? c.Long.UZERO : undefined
        },
        sint64: {
            name: "sint64",
            wireType: c.WIRE_TYPES.VARINT,
            defaultValue: c.Long ? c.Long.ZERO : undefined
        },
        bool: {
            name: "bool",
            wireType: c.WIRE_TYPES.VARINT,
            defaultValue: false
        },
        "double": {
            name: "double",
            wireType: c.WIRE_TYPES.BITS64,
            defaultValue: 0
        },
        string: {
            name: "string",
            wireType: c.WIRE_TYPES.LDELIM,
            defaultValue: ""
        },
        bytes: {
            name: "bytes",
            wireType: c.WIRE_TYPES.LDELIM,
            defaultValue: null
        },
        fixed32: {
            name: "fixed32",
            wireType: c.WIRE_TYPES.BITS32,
            defaultValue: 0
        },
        sfixed32: {
            name: "sfixed32",
            wireType: c.WIRE_TYPES.BITS32,
            defaultValue: 0
        },
        fixed64: {
            name: "fixed64",
            wireType: c.WIRE_TYPES.BITS64,
            defaultValue: c.Long ? c.Long.UZERO : undefined
        },
        sfixed64: {
            name: "sfixed64",
            wireType: c.WIRE_TYPES.BITS64,
            defaultValue: c.Long ? c.Long.ZERO : undefined
        },
        "float": {
            name: "float",
            wireType: c.WIRE_TYPES.BITS32,
            defaultValue: 0
        },
        "enum": {
            name: "enum",
            wireType: c.WIRE_TYPES.VARINT,
            defaultValue: 0
        },
        message: {
            name: "message",
            wireType: c.WIRE_TYPES.LDELIM,
            defaultValue: null
        },
        group: {
            name: "group",
            wireType: c.WIRE_TYPES.STARTGROUP,
            defaultValue: null
        }
    };
    c.MAP_KEY_TYPES = [c.TYPES.int32, c.TYPES.sint32, c.TYPES.sfixed32, c.TYPES.uint32, c.TYPES.fixed32, c.TYPES.int64, c.TYPES.sint64, c.TYPES.sfixed64, c.TYPES.uint64, c.TYPES.fixed64, c.TYPES.bool, c.TYPES.string, c.TYPES.bytes];
    c.ID_MIN = 1;
    c.ID_MAX = 536870911;
    c.convertFieldsToCamelCase = false;
    c.populateAccessors = true;
    c.populateDefaults = true;
    c.Util = (function() {
        var d = {};
        d.IS_NODE = !!(typeof process === "object" && process + "" === "[object process]" && !process.browser);
        d.XHR = function() {
            var f = [function() {
                return new XMLHttpRequest()
            }
            , function() {
                return new ActiveXObject("Msxml2.XMLHTTP")
            }
            , function() {
                return new ActiveXObject("Msxml3.XMLHTTP")
            }
            , function() {
                return new ActiveXObject("Microsoft.XMLHTTP")
            }
            ];
            var j = null;
            for (var g = 0; g < f.length; g++) {
                try {
                    j = f[g]()
                } catch (h) {
                    continue
                }
                break
            }
            if (!j) {
                throw Error("XMLHttpRequest is not supported")
            }
            return j
        }
        ;
        d.fetch = function(h, j) {
            if (j && typeof j != "function") {
                j = null
            }
            if (d.IS_NODE) {
                var f = require("fs");
                if (j) {
                    f.readFile(h, function(e, k) {
                        if (e) {
                            j(null)
                        } else {
                            j("" + k)
                        }
                    })
                } else {
                    try {
                        return f.readFileSync(h)
                    } catch (g) {
                        return null
                    }
                }
            } else {
                var i = d.XHR();
                i.open("GET", h, j ? true : false);
                i.setRequestHeader("Accept", "text/plain");
                if (typeof i.overrideMimeType === "function") {
                    i.overrideMimeType("text/plain")
                }
                if (j) {
                    i.onreadystatechange = function() {
                        if (i.readyState != 4) {
                            return
                        }
                        if (i.status == 200 || (i.status == 0 && typeof i.responseText === "string")) {
                            j(i.responseText)
                        } else {
                            j(null)
                        }
                    }
                    ;
                    if (i.readyState == 4) {
                        return
                    }
                    i.send(null)
                } else {
                    i.send(null);
                    if (i.status == 200 || (i.status == 0 && typeof i.responseText === "string")) {
                        return i.responseText
                    }
                    return null
                }
            }
        }
        ;
        d.toCamelCase = function(e) {
            return e.replace(/_([a-zA-Z])/g, function(g, f) {
                return f.toUpperCase()
            })
        }
        ;
        return d
    }
    )();
    c.Lang = {
        DELIM: /[\s\{\}=;:\[\],'"\(\)<>]/g,
        RULE: /^(?:required|optional|repeated|map)$/,
        TYPE: /^(?:double|float|int32|uint32|sint32|int64|uint64|sint64|fixed32|sfixed32|fixed64|sfixed64|bool|string|bytes)$/,
        NAME: /^[a-zA-Z_][a-zA-Z_0-9]*$/,
        TYPEDEF: /^[a-zA-Z][a-zA-Z_0-9]*$/,
        TYPEREF: /^(?:\.?[a-zA-Z_][a-zA-Z_0-9]*)+$/,
        FQTYPEREF: /^(?:\.[a-zA-Z][a-zA-Z_0-9]*)+$/,
        NUMBER: /^-?(?:[1-9][0-9]*|0|0[xX][0-9a-fA-F]+|0[0-7]+|([0-9]*(\.[0-9]*)?([Ee][+-]?[0-9]+)?)|inf|nan)$/,
        NUMBER_DEC: /^(?:[1-9][0-9]*|0)$/,
        NUMBER_HEX: /^0[xX][0-9a-fA-F]+$/,
        NUMBER_OCT: /^0[0-7]+$/,
        NUMBER_FLT: /^([0-9]*(\.[0-9]*)?([Ee][+-]?[0-9]+)?|inf|nan)$/,
        BOOL: /^(?:true|false)$/i,
        ID: /^(?:[1-9][0-9]*|0|0[xX][0-9a-fA-F]+|0[0-7]+)$/,
        NEGID: /^\-?(?:[1-9][0-9]*|0|0[xX][0-9a-fA-F]+|0[0-7]+)$/,
        WHITESPACE: /\s/,
        STRING: /(?:"([^"\\]*(?:\\.[^"\\]*)*)")|(?:'([^'\\]*(?:\\.[^'\\]*)*)')/g,
        STRING_DQ: /(?:"([^"\\]*(?:\\.[^"\\]*)*)")/g,
        STRING_SQ: /(?:'([^'\\]*(?:\\.[^'\\]*)*)')/g
    };
    c.DotProto = (function(i, h) {
        var k = {};
        var j = function(n) {
            this.source = n + "";
            this.index = 0;
            this.line = 1;
            this.stack = [];
            this._stringOpen = null
        };
        var m = j.prototype;
        m._readString = function() {
            var o = this._stringOpen === '"' ? h.STRING_DQ : h.STRING_SQ;
            o.lastIndex = this.index - 1;
            var n = o.exec(this.source);
            if (!n) {
                throw Error("unterminated string")
            }
            this.index = o.lastIndex;
            this.stack.push(this._stringOpen);
            this._stringOpen = null;
            return n[1]
        }
        ;
        m.next = function() {
            if (this.stack.length > 0) {
                return this.stack.shift()
            }
            if (this.index >= this.source.length) {
                return null
            }
            if (this._stringOpen !== null) {
                return this._readString()
            }
            var r, q, p;
            do {
                r = false;
                while (h.WHITESPACE.test(p = this.source.charAt(this.index))) {
                    if (p === "\n") {
                        ++this.line
                    }
                    if (++this.index === this.source.length) {
                        return null
                    }
                }
                if (this.source.charAt(this.index) === "/") {
                    ++this.index;
                    if (this.source.charAt(this.index) === "/") {
                        while (this.source.charAt(++this.index) !== "\n") {
                            if (this.index == this.source.length) {
                                return null
                            }
                        }
                        ++this.index;
                        ++this.line;
                        r = true
                    } else {
                        if ((p = this.source.charAt(this.index)) === "*") {
                            do {
                                if (p === "\n") {
                                    ++this.line
                                }
                                if (++this.index === this.source.length) {
                                    return null
                                }
                                q = p;
                                p = this.source.charAt(this.index)
                            } while (q !== "*" || p !== "/");
                            ++this.index;
                            r = true
                        } else {
                            return "/"
                        }
                    }
                }
            } while (r);
            if (this.index === this.source.length) {
                return null
            }
            var n = this.index;
            h.DELIM.lastIndex = 0;
            var s = h.DELIM.test(this.source.charAt(n++));
            if (!s) {
                while (n < this.source.length && !h.DELIM.test(this.source.charAt(n))) {
                    ++n
                }
            }
            var o = this.source.substring(this.index, this.index = n);
            if (o === '"' || o === "'") {
                this._stringOpen = o
            }
            return o
        }
        ;
        m.peek = function() {
            if (this.stack.length === 0) {
                var n = this.next();
                if (n === null) {
                    return null
                }
                this.stack.push(n)
            }
            return this.stack[0]
        }
        ;
        m.skip = function(n) {
            var o = this.next();
            if (o !== n) {
                throw Error("illegal '" + o + "', '" + n + "' expected")
            }
        }
        ;
        m.omit = function(n) {
            if (this.peek() === n) {
                this.next();
                return true
            }
            return false
        }
        ;
        m.toString = function() {
            return "Tokenizer (" + this.index + "/" + this.source.length + " at line " + this.line + ")"
        }
        ;
        k.Tokenizer = j;
        var g = function(n) {
            this.tn = new j(n);
            this.proto3 = false
        };
        var e = g.prototype;
        e.parse = function() {
            var n = {
                name: "[ROOT]",
                "package": null,
                messages: [],
                enums: [],
                imports: [],
                options: {},
                services: []
            };
            var p, o = true, q;
            try {
                while (p = this.tn.next()) {
                    switch (p) {
                    case "package":
                        if (!o || n["package"] !== null) {
                            throw Error("unexpected 'package'")
                        }
                        p = this.tn.next();
                        if (!h.TYPEREF.test(p)) {
                            throw Error("illegal package name: " + p)
                        }
                        this.tn.skip(";");
                        n["package"] = p;
                        break;
                    case "import":
                        if (!o) {
                            throw Error("unexpected 'import'")
                        }
                        p = this.tn.peek();
                        if (p === "public" || (q = p === "weak")) {
                            this.tn.next()
                        }
                        p = this._readString();
                        this.tn.skip(";");
                        if (!q) {
                            n.imports.push(p)
                        }
                        break;
                    case "syntax":
                        if (!o) {
                            throw Error("unexpected 'syntax'")
                        }
                        this.tn.skip("=");
                        if ((n.syntax = this._readString()) === "proto3") {
                            this.proto3 = true
                        }
                        this.tn.skip(";");
                        break;
                    case "message":
                        this._parseMessage(n, null);
                        o = false;
                        break;
                    case "enum":
                        this._parseEnum(n);
                        o = false;
                        break;
                    case "option":
                        this._parseOption(n);
                        break;
                    case "service":
                        this._parseService(n);
                        break;
                    case "extend":
                        this._parseExtend(n);
                        break;
                    default:
                        throw Error("unexpected '" + p + "'")
                    }
                }
            } catch (r) {
                r.message = "Parse error at line " + this.tn.line + ": " + r.message;
                throw r
            }
            delete n.name;
            return n
        }
        ;
        g.parse = function(n) {
            return new g(n).parse()
        }
        ;
        function d(p, o) {
            var q = -1
              , n = 1;
            if (p.charAt(0) == "-") {
                n = -1;
                p = p.substring(1)
            }
            if (h.NUMBER_DEC.test(p)) {
                q = parseInt(p)
            } else {
                if (h.NUMBER_HEX.test(p)) {
                    q = parseInt(p.substring(2), 16)
                } else {
                    if (h.NUMBER_OCT.test(p)) {
                        q = parseInt(p.substring(1), 8)
                    } else {
                        throw Error("illegal id value: " + (n < 0 ? "-" : "") + p)
                    }
                }
            }
            q = (n * q) | 0;
            if (!o && q < 0) {
                throw Error("illegal id value: " + (n < 0 ? "-" : "") + p)
            }
            return q
        }
        function l(o) {
            var n = 1;
            if (o.charAt(0) == "-") {
                n = -1;
                o = o.substring(1)
            }
            if (h.NUMBER_DEC.test(o)) {
                return n * parseInt(o, 10)
            } else {
                if (h.NUMBER_HEX.test(o)) {
                    return n * parseInt(o.substring(2), 16)
                } else {
                    if (h.NUMBER_OCT.test(o)) {
                        return n * parseInt(o.substring(1), 8)
                    } else {
                        if (o === "inf") {
                            return n * Infinity
                        } else {
                            if (o === "nan") {
                                return NaN
                            } else {
                                if (h.NUMBER_FLT.test(o)) {
                                    return n * parseFloat(o)
                                }
                            }
                        }
                    }
                }
            }
            throw Error("illegal number value: " + (n < 0 ? "-" : "") + o)
        }
        e._readString = function() {
            var o = "", n, p;
            do {
                p = this.tn.next();
                if (p !== "'" && p !== '"') {
                    throw Error("illegal string delimiter: " + p)
                }
                o += this.tn.next();
                this.tn.skip(p);
                n = this.tn.peek()
            } while (n === '"' || n === '"');
            return o
        }
        ;
        e._readValue = function(n) {
            var o = this.tn.peek(), p;
            if (o === '"' || o === "'") {
                return this._readString()
            }
            this.tn.next();
            if (h.NUMBER.test(o)) {
                return l(o)
            }
            if (h.BOOL.test(o)) {
                return (o.toLowerCase() === "true")
            }
            if (n && h.TYPEREF.test(o)) {
                return o
            }
            throw Error("illegal value: " + o)
        }
        ;
        e._parseOption = function(p, r) {
            var o = this.tn.next()
              , q = false;
            if (o === "(") {
                q = true;
                o = this.tn.next()
            }
            if (!h.TYPEREF.test(o)) {
                throw Error("illegal option name: " + o)
            }
            var n = o;
            if (q) {
                this.tn.skip(")");
                n = "(" + n + ")";
                o = this.tn.peek();
                if (h.FQTYPEREF.test(o)) {
                    n += o;
                    this.tn.next()
                }
            }
            this.tn.skip("=");
            this._parseOptionValue(p, n);
            if (!r) {
                this.tn.skip(";")
            }
        }
        ;
        function f(o, n, p) {
            if (typeof o[n] === "undefined") {
                o[n] = p
            } else {
                if (!Array.isArray(o[n])) {
                    o[n] = [o[n]]
                }
                o[n].push(p)
            }
        }
        e._parseOptionValue = function(p, n) {
            var o = this.tn.peek();
            if (o !== "{") {
                f(p.options, n, this._readValue(true))
            } else {
                this.tn.skip("{");
                while ((o = this.tn.next()) !== "}") {
                    if (!h.NAME.test(o)) {
                        throw Error("illegal option name: " + n + "." + o)
                    }
                    if (this.tn.omit(":")) {
                        f(p.options, n + "." + o, this._readValue(true))
                    } else {
                        this._parseOptionValue(p, n + "." + o)
                    }
                }
            }
        }
        ;
        e._parseService = function(p) {
            var o = this.tn.next();
            if (!h.NAME.test(o)) {
                throw Error("illegal service name at line " + this.tn.line + ": " + o)
            }
            var n = o;
            var q = {
                name: n,
                rpc: {},
                options: {}
            };
            this.tn.skip("{");
            while ((o = this.tn.next()) !== "}") {
                if (o === "option") {
                    this._parseOption(q)
                } else {
                    if (o === "rpc") {
                        this._parseServiceRPC(q)
                    } else {
                        throw Error("illegal service token: " + o)
                    }
                }
            }
            this.tn.omit(";");
            p.services.push(q)
        }
        ;
        e._parseServiceRPC = function(q) {
            var p = "rpc"
              , o = this.tn.next();
            if (!h.NAME.test(o)) {
                throw Error("illegal rpc service method name: " + o)
            }
            var n = o;
            var r = {
                request: null,
                response: null,
                request_stream: false,
                response_stream: false,
                options: {}
            };
            this.tn.skip("(");
            o = this.tn.next();
            if (o.toLowerCase() === "stream") {
                r.request_stream = true;
                o = this.tn.next()
            }
            if (!h.TYPEREF.test(o)) {
                throw Error("illegal rpc service request type: " + o)
            }
            r.request = o;
            this.tn.skip(")");
            o = this.tn.next();
            if (o.toLowerCase() !== "returns") {
                throw Error("illegal rpc service request type delimiter: " + o)
            }
            this.tn.skip("(");
            o = this.tn.next();
            if (o.toLowerCase() === "stream") {
                r.response_stream = true;
                o = this.tn.next()
            }
            r.response = o;
            this.tn.skip(")");
            o = this.tn.peek();
            if (o === "{") {
                this.tn.next();
                while ((o = this.tn.next()) !== "}") {
                    if (o === "option") {
                        this._parseOption(r)
                    } else {
                        throw Error("illegal rpc service token: " + o)
                    }
                }
                this.tn.omit(";")
            } else {
                this.tn.skip(";")
            }
            if (typeof q[p] === "undefined") {
                q[p] = {}
            }
            q[p][n] = r
        }
        ;
        e._parseMessage = function(p, o) {
            var r = !!o
              , n = this.tn.next();
            var q = {
                name: "",
                fields: [],
                enums: [],
                messages: [],
                options: {},
                services: [],
                oneofs: {}
            };
            if (!h.NAME.test(n)) {
                throw Error("illegal " + (r ? "group" : "message") + " name: " + n)
            }
            q.name = n;
            if (r) {
                this.tn.skip("=");
                o.id = d(this.tn.next());
                q.isGroup = true
            }
            n = this.tn.peek();
            if (n === "[" && o) {
                this._parseFieldOptions(o)
            }
            this.tn.skip("{");
            while ((n = this.tn.next()) !== "}") {
                if (h.RULE.test(n)) {
                    this._parseMessageField(q, n)
                } else {
                    if (n === "oneof") {
                        this._parseMessageOneOf(q)
                    } else {
                        if (n === "enum") {
                            this._parseEnum(q)
                        } else {
                            if (n === "message") {
                                this._parseMessage(q)
                            } else {
                                if (n === "option") {
                                    this._parseOption(q)
                                } else {
                                    if (n === "service") {
                                        this._parseService(q)
                                    } else {
                                        if (n === "extensions") {
                                            if (q.hasOwnProperty("extensions")) {
                                                q.extensions = q.extensions.concat(this._parseExtensionRanges())
                                            } else {
                                                q.extensions = this._parseExtensionRanges()
                                            }
                                        } else {
                                            if (n === "reserved") {
                                                this._parseIgnored()
                                            } else {
                                                if (n === "extend") {
                                                    this._parseExtend(q)
                                                } else {
                                                    if (h.TYPEREF.test(n)) {
                                                        if (!this.proto3) {
                                                            throw Error("illegal field rule: " + n)
                                                        }
                                                        this._parseMessageField(q, "optional", n)
                                                    } else {
                                                        throw Error("illegal message token: " + n)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            this.tn.omit(";");
            p.messages.push(q);
            return q
        }
        ;
        e._parseIgnored = function() {
            while (this.tn.peek() !== ";") {
                this.tn.next()
            }
            this.tn.skip(";")
        }
        ;
        e._parseMessageField = function(s, r, q) {
            if (!h.RULE.test(r)) {
                throw Error("illegal message field rule: " + r)
            }
            var p = {
                rule: r,
                type: "",
                name: "",
                options: {},
                id: 0
            };
            var o;
            if (r === "map") {
                if (q) {
                    throw Error("illegal type: " + q)
                }
                this.tn.skip("<");
                o = this.tn.next();
                if (!h.TYPE.test(o) && !h.TYPEREF.test(o)) {
                    throw Error("illegal message field type: " + o)
                }
                p.keytype = o;
                this.tn.skip(",");
                o = this.tn.next();
                if (!h.TYPE.test(o) && !h.TYPEREF.test(o)) {
                    throw Error("illegal message field: " + o)
                }
                p.type = o;
                this.tn.skip(">");
                o = this.tn.next();
                if (!h.NAME.test(o)) {
                    throw Error("illegal message field name: " + o)
                }
                p.name = o;
                this.tn.skip("=");
                p.id = d(this.tn.next());
                o = this.tn.peek();
                if (o === "[") {
                    this._parseFieldOptions(p)
                }
                this.tn.skip(";")
            } else {
                q = typeof q !== "undefined" ? q : this.tn.next();
                if (q === "group") {
                    var n = this._parseMessage(s, p);
                    if (!/^[A-Z]/.test(n.name)) {
                        throw Error("illegal group name: " + n.name)
                    }
                    p.type = n.name;
                    p.name = n.name.toLowerCase();
                    this.tn.omit(";")
                } else {
                    if (!h.TYPE.test(q) && !h.TYPEREF.test(q)) {
                        throw Error("illegal message field type: " + q)
                    }
                    p.type = q;
                    o = this.tn.next();
                    if (!h.NAME.test(o)) {
                        throw Error("illegal message field name: " + o)
                    }
                    p.name = o;
                    this.tn.skip("=");
                    p.id = d(this.tn.next());
                    o = this.tn.peek();
                    if (o === "[") {
                        this._parseFieldOptions(p)
                    }
                    this.tn.skip(";")
                }
            }
            s.fields.push(p);
            return p
        }
        ;
        e._parseMessageOneOf = function(r) {
            var q = this.tn.next();
            if (!h.NAME.test(q)) {
                throw Error("illegal oneof name: " + q)
            }
            var o = q, p;
            var n = [];
            this.tn.skip("{");
            while ((q = this.tn.next()) !== "}") {
                p = this._parseMessageField(r, "optional", q);
                p.oneof = o;
                n.push(p.id)
            }
            this.tn.omit(";");
            r.oneofs[o] = n
        }
        ;
        e._parseFieldOptions = function(o) {
            this.tn.skip("[");
            var n, p = true;
            while ((n = this.tn.peek()) !== "]") {
                if (!p) {
                    this.tn.skip(",")
                }
                this._parseOption(o, true);
                p = false
            }
            this.tn.next()
        }
        ;
        e._parseEnum = function(q) {
            var n = {
                name: "",
                values: [],
                options: {}
            };
            var o = this.tn.next();
            if (!h.NAME.test(o)) {
                throw Error("illegal name: " + o)
            }
            n.name = o;
            this.tn.skip("{");
            while ((o = this.tn.next()) !== "}") {
                if (o === "option") {
                    this._parseOption(n)
                } else {
                    if (!h.NAME.test(o)) {
                        throw Error("illegal name: " + o)
                    }
                    this.tn.skip("=");
                    var p = {
                        name: o,
                        id: d(this.tn.next(), true)
                    };
                    o = this.tn.peek();
                    if (o === "[") {
                        this._parseFieldOptions({
                            options: {}
                        })
                    }
                    this.tn.skip(";");
                    n.values.push(p)
                }
            }
            this.tn.omit(";");
            q.enums.push(n)
        }
        ;
        e._parseExtensionRanges = function() {
            var n = [];
            var p, o, q;
            do {
                o = [];
                while (true) {
                    p = this.tn.next();
                    switch (p) {
                    case "min":
                        q = i.ID_MIN;
                        break;
                    case "max":
                        q = i.ID_MAX;
                        break;
                    default:
                        q = l(p);
                        break
                    }
                    o.push(q);
                    if (o.length === 2) {
                        break
                    }
                    if (this.tn.peek() !== "to") {
                        o.push(q);
                        break
                    }
                    this.tn.next()
                }
                n.push(o)
            } while (this.tn.omit(","));
            this.tn.skip(";");
            return n
        }
        ;
        e._parseExtend = function(p) {
            var n = this.tn.next();
            if (!h.TYPEREF.test(n)) {
                throw Error("illegal extend reference: " + n)
            }
            var o = {
                ref: n,
                fields: []
            };
            this.tn.skip("{");
            while ((n = this.tn.next()) !== "}") {
                if (h.RULE.test(n)) {
                    this._parseMessageField(o, n)
                } else {
                    if (h.TYPEREF.test(n)) {
                        if (!this.proto3) {
                            throw Error("illegal field rule: " + n)
                        }
                        this._parseMessageField(o, "optional", n)
                    } else {
                        throw Error("illegal extend token: " + n)
                    }
                }
            }
            this.tn.omit(";");
            p.messages.push(o);
            return o
        }
        ;
        e.toString = function() {
            return "Parser at line " + this.tn.line
        }
        ;
        k.Parser = g;
        return k
    }
    )(c, c.Lang);
    c.Reflect = (function(l) {
        var g = {};
        var h = function(D, F, E) {
            this.builder = D;
            this.parent = F;
            this.name = E;
            this.className
        };
        var f = h.prototype;
        f.fqn = function() {
            var D = this.name
              , E = this;
            do {
                E = E.parent;
                if (E == null) {
                    break
                }
                D = E.name + "." + D
            } while (true);
            return D
        }
        ;
        f.toString = function(D) {
            return (D ? this.className + " " : "") + this.fqn()
        }
        ;
        f.build = function() {
            throw Error(this.toString(true) + " cannot be built directly")
        }
        ;
        g.T = h;
        var p = function(E, H, G, F, D) {
            h.call(this, E, H, G);
            this.className = "Namespace";
            this.children = [];
            this.options = F || {};
            this.syntax = D || "proto2"
        };
        var u = p.prototype = Object.create(h.prototype);
        u.getChildren = function(G) {
            G = G || null;
            if (G == null) {
                return this.children.slice()
            }
            var F = [];
            for (var E = 0, D = this.children.length; E < D; ++E) {
                if (this.children[E]instanceof G) {
                    F.push(this.children[E])
                }
            }
            return F
        }
        ;
        u.addChild = function(E) {
            var D;
            if (D = this.getChild(E.name)) {
                if (D instanceof d.Field && D.name !== D.originalName && this.getChild(D.originalName) === null) {
                    D.name = D.originalName
                } else {
                    if (E instanceof d.Field && E.name !== E.originalName && this.getChild(E.originalName) === null) {
                        E.name = E.originalName
                    } else {
                        throw Error("Duplicate name in namespace " + this.toString(true) + ": " + E.name)
                    }
                }
            }
            this.children.push(E)
        }
        ;
        u.getChild = function(G) {
            var F = typeof G === "number" ? "id" : "name";
            for (var E = 0, D = this.children.length; E < D; ++E) {
                if (this.children[E][F] === G) {
                    return this.children[E]
                }
            }
            return null
        }
        ;
        u.resolve = function(G, D) {
            var E = typeof G === "string" ? G.split(".") : G
              , I = this
              , F = 0;
            if (E[F] === "") {
                while (I.parent !== null) {
                    I = I.parent
                }
                F++
            }
            var H;
            do {
                do {
                    if (!(I instanceof g.Namespace)) {
                        I = null;
                        break
                    }
                    H = I.getChild(E[F]);
                    if (!H || !(H instanceof g.T) || (D && !(H instanceof g.Namespace))) {
                        I = null;
                        break
                    }
                    I = H;
                    F++
                } while (F < E.length);
                if (I != null) {
                    break
                }
                if (this.parent !== null) {
                    return this.parent.resolve(G, D)
                }
            } while (I != null);
            return I
        }
        ;
        u.qn = function(F) {
            var E = []
              , H = F;
            do {
                E.unshift(H.name);
                H = H.parent
            } while (H !== null);
            for (var D = 1; D <= E.length; D++) {
                var G = E.slice(E.length - D);
                if (F === this.resolve(G, F instanceof g.Namespace)) {
                    return G.join(".")
                }
            }
            return F.fqn()
        }
        ;
        u.build = function() {
            var G = {};
            var F = this.children;
            for (var E = 0, D = F.length, H; E < D; ++E) {
                H = F[E];
                if (H instanceof p) {
                    G[H.name] = H.build()
                }
            }
            if (Object.defineProperty) {
                Object.defineProperty(G, "$options", {
                    value: this.buildOpt()
                })
            }
            return G
        }
        ;
        u.buildOpt = function() {
            var G = {}
              , H = Object.keys(this.options);
            for (var F = 0, D = H.length; F < D; ++F) {
                var E = H[F]
                  , I = this.options[H[F]];
                G[E] = I
            }
            return G
        }
        ;
        u.getOption = function(D) {
            if (typeof D === "undefined") {
                return this.options
            }
            return typeof this.options[D] !== "undefined" ? this.options[D] : null
        }
        ;
        g.Namespace = p;
        var s = function(H, F, G, D, E) {
            this.type = H;
            this.resolvedType = F;
            this.isMapKey = G;
            this.syntax = D;
            this.name = E;
            if (G && l.MAP_KEY_TYPES.indexOf(H) < 0) {
                throw Error("Invalid map key type: " + H.name)
            }
        };
        var x = s.prototype;
        function w(D) {
            if (typeof D === "string") {
                D = l.TYPES[D]
            }
            if (typeof D.defaultValue === "undefined") {
                throw Error("default value for type " + D.name + " is not supported")
            }
            if (D == l.TYPES.bytes) {
                return new b(0)
            }
            return D.defaultValue
        }
        s.defaultFieldValue = w;
        function k(E, D) {
            if (E && typeof E.low === "number" && typeof E.high === "number" && typeof E.unsigned === "boolean" && E.low === E.low && E.high === E.high) {
                return new l.Long(E.low,E.high,typeof D === "undefined" ? E.unsigned : D)
            }
            if (typeof E === "string") {
                return l.Long.fromString(E, D || false, 10)
            }
            if (typeof E === "number") {
                return l.Long.fromNumber(E, D || false)
            }
            throw Error("not convertible to Long")
        }
        x.toString = function() {
            return (this.name || "") + (this.isMapKey ? "map" : "value") + " element"
        }
        ;
        x.verifyValue = function(H) {
            var F = this;
            function D(L, K) {
                throw Error("Illegal value for " + F.toString(true) + " of type " + F.type.name + ": " + L + " (" + K + ")")
            }
            switch (this.type) {
            case l.TYPES.int32:
            case l.TYPES.sint32:
            case l.TYPES.sfixed32:
                if (typeof H !== "number" || (H === H && H % 1 !== 0)) {
                    D(typeof H, "not an integer")
                }
                return H > 4294967295 ? H | 0 : H;
            case l.TYPES.uint32:
            case l.TYPES.fixed32:
                if (typeof H !== "number" || (H === H && H % 1 !== 0)) {
                    D(typeof H, "not an integer")
                }
                return H < 0 ? H >>> 0 : H;
            case l.TYPES.int64:
            case l.TYPES.sint64:
            case l.TYPES.sfixed64:
                if (l.Long) {
                    try {
                        return k(H, false)
                    } catch (J) {
                        D(typeof H, J.message)
                    }
                } else {
                    D(typeof H, "requires Long.js")
                }
            case l.TYPES.uint64:
            case l.TYPES.fixed64:
                if (l.Long) {
                    try {
                        return k(H, true)
                    } catch (J) {
                        D(typeof H, J.message)
                    }
                } else {
                    D(typeof H, "requires Long.js")
                }
            case l.TYPES.bool:
                if (typeof H !== "boolean") {
                    D(typeof H, "not a boolean")
                }
                return H;
            case l.TYPES["float"]:
            case l.TYPES["double"]:
                if (typeof H !== "number") {
                    D(typeof H, "not a number")
                }
                return H;
            case l.TYPES.string:
                if (typeof H !== "string" && !(H && H instanceof String)) {
                    D(typeof H, "not a string")
                }
                return "" + H;
            case l.TYPES.bytes:
                if (b.isByteBuffer(H)) {
                    return H
                }
                return b.wrap(H, "base64");
            case l.TYPES["enum"]:
                var E = this.resolvedType.getChildren(l.Reflect.Enum.Value);
                for (G = 0; G < E.length; G++) {
                    if (E[G].name == H) {
                        return E[G].id
                    } else {
                        if (E[G].id == H) {
                            return E[G].id
                        }
                    }
                }
                if (this.syntax === "proto3") {
                    if (typeof H !== "number" || (H === H && H % 1 !== 0)) {
                        D(typeof H, "not an integer")
                    }
                    if (H > 4294967295 || H < 0) {
                        D(typeof H, "not in range for uint32")
                    }
                    return H
                } else {
                    D(H, "not a valid enum value")
                }
            case l.TYPES.group:
            case l.TYPES.message:
                if (!H || typeof H !== "object") {
                    D(typeof H, "object expected")
                }
                if (H instanceof this.resolvedType.clazz) {
                    return H
                }
                if (H instanceof l.Builder.Message) {
                    var I = {};
                    for (var G in H) {
                        if (H.hasOwnProperty(G)) {
                            I[G] = H[G]
                        }
                    }
                    H = I
                }
                return new (this.resolvedType.clazz)(H)
            }
            throw Error("[INTERNAL] Illegal value for " + this.toString(true) + ": " + H + " (undefined type " + this.type + ")")
        }
        ;
        x.calculateLength = function(F, D) {
            if (D === null) {
                return 0
            }
            var E;
            switch (this.type) {
            case l.TYPES.int32:
                return D < 0 ? b.calculateVarint64(D) : b.calculateVarint32(D);
            case l.TYPES.uint32:
                return b.calculateVarint32(D);
            case l.TYPES.sint32:
                return b.calculateVarint32(b.zigZagEncode32(D));
            case l.TYPES.fixed32:
            case l.TYPES.sfixed32:
            case l.TYPES["float"]:
                return 4;
            case l.TYPES.int64:
            case l.TYPES.uint64:
                return b.calculateVarint64(D);
            case l.TYPES.sint64:
                return b.calculateVarint64(b.zigZagEncode64(D));
            case l.TYPES.fixed64:
            case l.TYPES.sfixed64:
                return 8;
            case l.TYPES.bool:
                return 1;
            case l.TYPES["enum"]:
                return b.calculateVarint32(D);
            case l.TYPES["double"]:
                return 8;
            case l.TYPES.string:
                E = b.calculateUTF8Bytes(D);
                return b.calculateVarint32(E) + E;
            case l.TYPES.bytes:
                if (D.remaining() < 0) {
                    throw Error("Illegal value for " + this.toString(true) + ": " + D.remaining() + " bytes remaining")
                }
                return b.calculateVarint32(D.remaining()) + D.remaining();
            case l.TYPES.message:
                E = this.resolvedType.calculate(D);
                return b.calculateVarint32(E) + E;
            case l.TYPES.group:
                E = this.resolvedType.calculate(D);
                return E + b.calculateVarint32((F << 3) | l.WIRE_TYPES.ENDGROUP)
            }
            throw Error("[INTERNAL] Illegal value to encode in " + this.toString(true) + ": " + D + " (unknown type)")
        }
        ;
        x.encodeValue = function(H, E, D) {
            if (E === null) {
                return D
            }
            switch (this.type) {
            case l.TYPES.int32:
                if (E < 0) {
                    D.writeVarint64(E)
                } else {
                    D.writeVarint32(E)
                }
                break;
            case l.TYPES.uint32:
                D.writeVarint32(E);
                break;
            case l.TYPES.sint32:
                D.writeVarint32ZigZag(E);
                break;
            case l.TYPES.fixed32:
                D.writeUint32(E);
                break;
            case l.TYPES.sfixed32:
                D.writeInt32(E);
                break;
            case l.TYPES.int64:
            case l.TYPES.uint64:
                D.writeVarint64(E);
                break;
            case l.TYPES.sint64:
                D.writeVarint64ZigZag(E);
                break;
            case l.TYPES.fixed64:
                D.writeUint64(E);
                break;
            case l.TYPES.sfixed64:
                D.writeInt64(E);
                break;
            case l.TYPES.bool:
                if (typeof E === "string") {
                    D.writeVarint32(E.toLowerCase() === "false" ? 0 : !!E)
                } else {
                    D.writeVarint32(E ? 1 : 0)
                }
                break;
            case l.TYPES["enum"]:
                D.writeVarint32(E);
                break;
            case l.TYPES["float"]:
                D.writeFloat32(E);
                break;
            case l.TYPES["double"]:
                D.writeFloat64(E);
                break;
            case l.TYPES.string:
                D.writeVString(E);
                break;
            case l.TYPES.bytes:
                if (E.remaining() < 0) {
                    throw Error("Illegal value for " + this.toString(true) + ": " + E.remaining() + " bytes remaining")
                }
                var F = E.offset;
                D.writeVarint32(E.remaining());
                D.append(E);
                E.offset = F;
                break;
            case l.TYPES.message:
                var G = new b().LE();
                this.resolvedType.encode(E, G);
                D.writeVarint32(G.offset);
                D.append(G.flip());
                break;
            case l.TYPES.group:
                this.resolvedType.encode(E, D);
                D.writeVarint32((H << 3) | l.WIRE_TYPES.ENDGROUP);
                break;
            default:
                throw Error("[INTERNAL] Illegal value to encode in " + this.toString(true) + ": " + E + " (unknown type)")
            }
            return D
        }
        ;
        x.decode = function(E, D, H) {
            if (D != this.type.wireType) {
                throw Error("Unexpected wire type for element")
            }
            var F, G;
            switch (this.type) {
            case l.TYPES.int32:
                return E.readVarint32() | 0;
            case l.TYPES.uint32:
                return E.readVarint32() >>> 0;
            case l.TYPES.sint32:
                return E.readVarint32ZigZag() | 0;
            case l.TYPES.fixed32:
                return E.readUint32() >>> 0;
            case l.TYPES.sfixed32:
                return E.readInt32() | 0;
            case l.TYPES.int64:
                return E.readVarint64();
            case l.TYPES.uint64:
                return E.readVarint64().toUnsigned();
            case l.TYPES.sint64:
                return E.readVarint64ZigZag();
            case l.TYPES.fixed64:
                return E.readUint64();
            case l.TYPES.sfixed64:
                return E.readInt64();
            case l.TYPES.bool:
                return !!E.readVarint32();
            case l.TYPES["enum"]:
                return E.readVarint32();
            case l.TYPES["float"]:
                return E.readFloat();
            case l.TYPES["double"]:
                return E.readDouble();
            case l.TYPES.string:
                return E.readVString();
            case l.TYPES.bytes:
                G = E.readVarint32();
                if (E.remaining() < G) {
                    throw Error("Illegal number of bytes for " + this.toString(true) + ": " + G + " required but got only " + E.remaining())
                }
                F = E.clone();
                F.limit = F.offset + G;
                E.offset += G;
                return F;
            case l.TYPES.message:
                G = E.readVarint32();
                return this.resolvedType.decode(E, G);
            case l.TYPES.group:
                return this.resolvedType.decode(E, -1, H)
            }
            throw Error("[INTERNAL] Illegal decode type")
        }
        ;
        x.valueFromString = function(D) {
            if (!this.isMapKey) {
                throw Error("valueFromString() called on non-map-key element")
            }
            switch (this.type) {
            case l.TYPES.int32:
            case l.TYPES.sint32:
            case l.TYPES.sfixed32:
            case l.TYPES.uint32:
            case l.TYPES.fixed32:
                return this.verifyValue(parseInt(D));
            case l.TYPES.int64:
            case l.TYPES.sint64:
            case l.TYPES.sfixed64:
            case l.TYPES.uint64:
            case l.TYPES.fixed64:
                return this.verifyValue(D);
            case l.TYPES.bool:
                return D === "true";
            case l.TYPES.string:
                return this.verifyValue(D);
            case l.TYPES.bytes:
                return b.fromBinary(D)
            }
        }
        ;
        x.valueToString = function(D) {
            if (!this.isMapKey) {
                throw Error("valueToString() called on non-map-key element")
            }
            if (this.type === l.TYPES.bytes) {
                return D.toString("binary")
            } else {
                return D.toString()
            }
        }
        ;
        g.Element = s;
        var d = function(E, H, G, F, I, D) {
            p.call(this, E, H, G, F, D);
            this.className = "Message";
            this.extensions = undefined;
            this.clazz = null;
            this.isGroup = !!I;
            this._fields = null;
            this._fieldsById = null;
            this._fieldsByName = null
        };
        var C = d.prototype = Object.create(p.prototype);
        C.build = function(D) {
            if (this.clazz && !D) {
                return this.clazz
            }
            var F = (function(P, J) {
                var N = J.getChildren(P.Reflect.Message.Field)
                  , S = J.getChildren(P.Reflect.Message.OneOf);
                var Q = function(W, aa) {
                    P.Builder.Message.call(this);
                    for (var X = 0, T = S.length; X < T; ++X) {
                        this[S[X].name] = null
                    }
                    for (X = 0,
                    T = N.length; X < T; ++X) {
                        var Z = N[X];
                        this[Z.name] = Z.repeated ? [] : (Z.map ? new P.Map(Z) : null);
                        if ((Z.required || J.syntax === "proto3") && Z.defaultValue !== null) {
                            this[Z.name] = Z.defaultValue
                        }
                    }
                    if (arguments.length > 0) {
                        var Y;
                        if (arguments.length === 1 && W !== null && typeof W === "object" && (typeof W.encode !== "function" || W instanceof Q) && !Array.isArray(W) && !(W instanceof P.Map) && !b.isByteBuffer(W) && !(W instanceof ArrayBuffer) && !(P.Long && W instanceof P.Long)) {
                            this.$set(W)
                        } else {
                            for (X = 0,
                            T = arguments.length; X < T; ++X) {
                                if (typeof (Y = arguments[X]) !== "undefined") {
                                    this.$set(N[X].name, Y)
                                }
                            }
                        }
                    }
                };
                var M = Q.prototype = Object.create(P.Builder.Message.prototype);
                M.add = function(T, W, Y) {
                    var X = J._fieldsByName[T];
                    if (!Y) {
                        if (!X) {
                            throw Error(this + "#" + T + " is undefined")
                        }
                        if (!(X instanceof P.Reflect.Message.Field)) {
                            throw Error(this + "#" + T + " is not a field: " + X.toString(true))
                        }
                        if (!X.repeated) {
                            throw Error(this + "#" + T + " is not a repeated field")
                        }
                        W = X.verifyValue(W, true)
                    }
                    if (this[T] === null) {
                        this[T] = []
                    }
                    this[T].push(W);
                    return this
                }
                ;
                M.$add = M.add;
                M.set = function(aa, W, Z) {
                    if (aa && typeof aa === "object") {
                        Z = W;
                        for (var Y in aa) {
                            if (aa.hasOwnProperty(Y) && typeof (W = aa[Y]) !== "undefined") {
                                this.$set(Y, W, Z)
                            }
                        }
                        return this
                    }
                    var X = J._fieldsByName[aa];
                    if (!Z) {
                        if (!X) {
                            throw Error(this + "#" + aa + " is not a field: undefined")
                        }
                        if (!(X instanceof P.Reflect.Message.Field)) {
                            throw Error(this + "#" + aa + " is not a field: " + X.toString(true))
                        }
                        this[X.name] = (W = X.verifyValue(W))
                    } else {
                        this[aa] = W
                    }
                    if (X && X.oneof) {
                        var T = this[X.oneof.name];
                        if (W !== null) {
                            if (T !== null && T !== X.name) {
                                this[T] = null
                            }
                            this[X.oneof.name] = X.name
                        } else {
                            if (T === aa) {
                                this[X.oneof.name] = null
                            }
                        }
                    }
                    return this
                }
                ;
                M.$set = M.set;
                M.get = function(T, X) {
                    if (X) {
                        return this[T]
                    }
                    var W = J._fieldsByName[T];
                    if (!W || !(W instanceof P.Reflect.Message.Field)) {
                        throw Error(this + "#" + T + " is not a field: undefined")
                    }
                    if (!(W instanceof P.Reflect.Message.Field)) {
                        throw Error(this + "#" + T + " is not a field: " + W.toString(true))
                    }
                    return this[W.name]
                }
                ;
                M.$get = M.get;
                for (var K = 0; K < N.length; K++) {
                    var R = N[K];
                    if (R instanceof P.Reflect.Message.ExtensionField) {
                        continue
                    }
                    if (J.builder.options.populateAccessors) {
                        (function(Y) {
                            var W = Y.originalName.replace(/(_[a-zA-Z])/g, function(aa) {
                                return aa.toUpperCase().replace("_", "")
                            });
                            W = W.substring(0, 1).toUpperCase() + W.substring(1);
                            var X = Y.originalName.replace(/([A-Z])/g, function(aa) {
                                return "_" + aa
                            });
                            var Z = function(aa, ab) {
                                this[Y.name] = ab ? aa : Y.verifyValue(aa);
                                return this
                            };
                            var T = function() {
                                return this[Y.name]
                            };
                            if (J.getChild("set" + W) === null) {
                                M["set" + W] = Z
                            }
                            if (J.getChild("set_" + X) === null) {
                                M["set_" + X] = Z
                            }
                            if (J.getChild("get" + W) === null) {
                                M["get" + W] = T
                            }
                            if (J.getChild("get_" + X) === null) {
                                M["get_" + X] = T
                            }
                        }
                        )(R)
                    }
                }
                M.encode = function(W, Y) {
                    if (typeof W === "boolean") {
                        Y = W,
                        W = undefined
                    }
                    var T = false;
                    if (!W) {
                        W = new b(),
                        T = true
                    }
                    var X = W.littleEndian;
                    try {
                        J.encode(this, W.LE(), Y);
                        return (T ? W.flip() : W).LE(X)
                    } catch (Z) {
                        W.LE(X);
                        throw (Z)
                    }
                }
                ;
                Q.encode = function(X, T, W) {
                    return new Q(X).encode(T, W)
                }
                ;
                M.calculate = function() {
                    return J.calculate(this)
                }
                ;
                M.encodeDelimited = function(W, Y) {
                    var T = false;
                    if (!W) {
                        W = new b(),
                        T = true
                    }
                    var X = new b().LE();
                    J.encode(this, X, Y).flip();
                    W.writeVarint32(X.remaining());
                    W.append(X);
                    return T ? W.flip() : W
                }
                ;
                M.encodeAB = function() {
                    try {
                        return this.encode().toArrayBuffer()
                    } catch (T) {
                        if (T.encoded) {
                            T.encoded = T.encoded.toArrayBuffer()
                        }
                        throw (T)
                    }
                }
                ;
                M.toArrayBuffer = M.encodeAB;
                M.encodeNB = function() {
                    try {
                        return this.encode().toBuffer()
                    } catch (T) {
                        if (T.encoded) {
                            T.encoded = T.encoded.toBuffer()
                        }
                        throw (T)
                    }
                }
                ;
                M.toBuffer = M.encodeNB;
                M.encode64 = function() {
                    try {
                        return this.encode().toBase64()
                    } catch (T) {
                        if (T.encoded) {
                            T.encoded = T.encoded.toBase64()
                        }
                        throw (T)
                    }
                }
                ;
                M.toBase64 = M.encode64;
                M.encodeHex = function() {
                    try {
                        return this.encode().toHex()
                    } catch (T) {
                        if (T.encoded) {
                            T.encoded = T.encoded.toHex()
                        }
                        throw (T)
                    }
                }
                ;
                M.toHex = M.encodeHex;
                function U(X, ab, Z, af) {
                    if (X === null || typeof X !== "object") {
                        if (af && af instanceof P.Reflect.Enum) {
                            var T = P.Reflect.Enum.getName(af.object, X);
                            if (T !== null) {
                                return T
                            }
                        }
                        return X
                    }
                    if (b.isByteBuffer(X)) {
                        return ab ? X.toBase64() : X.toBuffer()
                    }
                    if (P.Long.isLong(X)) {
                        return Z ? X.toString() : P.Long.fromValue(X)
                    }
                    var ad;
                    if (Array.isArray(X)) {
                        ad = [];
                        X.forEach(function(ah, ag) {
                            ad[ag] = U(ah, ab, Z, af)
                        });
                        return ad
                    }
                    ad = {};
                    if (X instanceof P.Map) {
                        var Y = X.entries();
                        for (var aa = Y.next(); !aa.done; aa = Y.next()) {
                            ad[X.keyElem.valueToString(aa.value[0])] = U(aa.value[1], ab, Z, X.valueElem.resolvedType)
                        }
                        return ad
                    }
                    var ac = X.$type
                      , ae = undefined;
                    for (var W in X) {
                        if (X.hasOwnProperty(W)) {
                            if (ac && (ae = ac.getChild(W))) {
                                ad[W] = U(X[W], ab, Z, ae.resolvedType)
                            } else {
                                ad[W] = U(X[W], ab, Z)
                            }
                        }
                    }
                    return ad
                }
                M.toRaw = function(T, W) {
                    return U(this, !!T, !!W, this.$type)
                }
                ;
                M.encodeJSON = function() {
                    return JSON.stringify(U(this, true, true, this.$type))
                }
                ;
                Q.decode = function(T, Y, W) {
                    if (typeof Y === "string") {
                        W = Y,
                        Y = -1
                    }
                    if (typeof T === "string") {
                        T = b.wrap(T, W ? W : "base64")
                    } else {
                        if (!b.isByteBuffer(T)) {
                            T = b.wrap(T)
                        }
                    }
                    var X = T.littleEndian;
                    try {
                        var aa = J.decode(T.LE(), Y);
                        T.LE(X);
                        return aa
                    } catch (Z) {
                        T.LE(X);
                        throw (Z)
                    }
                }
                ;
                Q.decodeDelimited = function(W, X) {
                    if (typeof W === "string") {
                        W = b.wrap(W, X ? X : "base64")
                    } else {
                        if (!b.isByteBuffer(W)) {
                            W = b.wrap(W)
                        }
                    }
                    if (W.remaining() < 1) {
                        return null
                    }
                    var aa = W.offset
                      , T = W.readVarint32();
                    if (W.remaining() < T) {
                        W.offset = aa;
                        return null
                    }
                    try {
                        var Z = J.decode(W.slice(W.offset, W.offset + T).LE());
                        W.offset += T;
                        return Z
                    } catch (Y) {
                        W.offset += T;
                        throw Y
                    }
                }
                ;
                Q.decode64 = function(T) {
                    return Q.decode(T, "base64")
                }
                ;
                Q.decodeHex = function(T) {
                    return Q.decode(T, "hex")
                }
                ;
                Q.decodeJSON = function(T) {
                    return new Q(JSON.parse(T))
                }
                ;
                M.toString = function() {
                    return J.toString()
                }
                ;
                var I;
                var L;
                var V;
                var O;
                if (Object.defineProperty) {
                    Object.defineProperty(Q, "$options", {
                        value: J.buildOpt()
                    }),
                    Object.defineProperty(M, "$options", {
                        value: Q["$options"]
                    }),
                    Object.defineProperty(Q, "$type", {
                        value: J
                    }),
                    Object.defineProperty(M, "$type", {
                        value: J
                    })
                }
                return Q
            }
            )(l, this);
            this._fields = [];
            this._fieldsById = {};
            this._fieldsByName = {};
            for (var G = 0, E = this.children.length, H; G < E; G++) {
                H = this.children[G];
                if (H instanceof q || H instanceof d || H instanceof o) {
                    if (F.hasOwnProperty(H.name)) {
                        throw Error("Illegal reflect child of " + this.toString(true) + ": " + H.toString(true) + " cannot override static property '" + H.name + "'")
                    }
                    F[H.name] = H.build()
                } else {
                    if (H instanceof d.Field) {
                        H.build(),
                        this._fields.push(H),
                        this._fieldsById[H.id] = H,
                        this._fieldsByName[H.name] = H
                    } else {
                        if (!(H instanceof d.OneOf) && !(H instanceof n)) {
                            throw Error("Illegal reflect child of " + this.toString(true) + ": " + this.children[G].toString(true))
                        }
                    }
                }
            }
            return this.clazz = F
        }
        ;
        C.encode = function(L, H, I) {
            var D = null, K;
            for (var J = 0, G = this._fields.length, E; J < G; ++J) {
                K = this._fields[J];
                E = L[K.name];
                if (K.required && E === null) {
                    if (D === null) {
                        D = K
                    }
                } else {
                    K.encode(I ? E : K.verifyValue(E), H, L)
                }
            }
            if (D !== null) {
                var F = Error("Missing at least one required field for " + this.toString(true) + ": " + D);
                F.encoded = H;
                throw (F)
            }
            return H
        }
        ;
        C.calculate = function(F) {
            for (var I = 0, E = 0, D = this._fields.length, G, H; E < D; ++E) {
                G = this._fields[E];
                H = F[G.name];
                if (G.required && H === null) {
                    throw Error("Missing at least one required field for " + this.toString(true) + ": " + G)
                } else {
                    I += G.calculate(H, F)
                }
            }
            return I
        }
        ;
        function A(G, F) {
            var E = F.readVarint32()
              , D = E & 7
              , H = E >>> 3;
            switch (D) {
            case l.WIRE_TYPES.VARINT:
                do {
                    E = F.readUint8()
                } while ((E & 128) === 128);
                break;
            case l.WIRE_TYPES.BITS64:
                F.offset += 8;
                break;
            case l.WIRE_TYPES.LDELIM:
                E = F.readVarint32();
                F.offset += E;
                break;
            case l.WIRE_TYPES.STARTGROUP:
                A(H, F);
                break;
            case l.WIRE_TYPES.ENDGROUP:
                if (H === G) {
                    return false
                } else {
                    throw Error("Illegal GROUPEND after unknown group: " + H + " (" + G + " expected)")
                }
            case l.WIRE_TYPES.BITS32:
                F.offset += 4;
                break;
            default:
                throw Error("Illegal wire type in unknown group " + G + ": " + D)
            }
            return true
        }
        C.decode = function(J, F, L) {
            if (typeof F !== "number") {
                F = -1
            }
            var D = J.offset, G = new (this.clazz)(), R, Q, E, O;
            while (J.offset < D + F || (F === -1 && J.remaining() > 0)) {
                R = J.readVarint32();
                Q = R & 7;
                E = R >>> 3;
                if (Q === l.WIRE_TYPES.ENDGROUP) {
                    if (E !== L) {
                        throw Error("Illegal group end indicator for " + this.toString(true) + ": " + E + " (" + (L ? L + " expected" : "not a group") + ")")
                    }
                    break
                }
                if (!(O = this._fieldsById[E])) {
                    switch (Q) {
                    case l.WIRE_TYPES.VARINT:
                        J.readVarint32();
                        break;
                    case l.WIRE_TYPES.BITS32:
                        J.offset += 4;
                        break;
                    case l.WIRE_TYPES.BITS64:
                        J.offset += 8;
                        break;
                    case l.WIRE_TYPES.LDELIM:
                        var M = J.readVarint32();
                        J.offset += M;
                        break;
                    case l.WIRE_TYPES.STARTGROUP:
                        while (A(E, J)) {}
                        break;
                    default:
                        throw Error("Illegal wire type for unknown field " + E + " in " + this.toString(true) + "#decode: " + Q)
                    }
                    continue
                }
                if (O.repeated && !O.options.packed) {
                    G[O.name].push(O.decode(Q, J))
                } else {
                    if (O.map) {
                        var N = O.decode(Q, J);
                        G[O.name].set(N[0], N[1])
                    } else {
                        G[O.name] = O.decode(Q, J);
                        if (O.oneof) {
                            var P = G[O.oneof.name];
                            if (P !== null && P !== O.name) {
                                G[P] = null
                            }
                            G[O.oneof.name] = O.name
                        }
                    }
                }
            }
            for (var K = 0, I = this._fields.length; K < I; ++K) {
                O = this._fields[K];
                if (G[O.name] === null) {
                    if (this.syntax === "proto3") {
                        G[O.name] = O.defaultValue
                    } else {
                        if (O.required) {
                            var H = Error("Missing at least one required field for " + this.toString(true) + ": " + O.name);
                            H.decoded = G;
                            throw (H)
                        } else {
                            if (l.populateDefaults && O.defaultValue !== null) {
                                G[O.name] = O.defaultValue
                            }
                        }
                    }
                }
            }
            return G
        }
        ;
        g.Message = d;
        var j = function(H, L, K, F, J, D, E, M, I, G) {
            h.call(this, H, L, D);
            this.className = "Message.Field";
            this.required = K === "required";
            this.repeated = K === "repeated";
            this.map = K === "map";
            this.keyType = F || null;
            this.type = J;
            this.resolvedType = null;
            this.id = E;
            this.options = M || {};
            this.defaultValue = null;
            this.oneof = I || null;
            this.syntax = G || "proto2";
            this.originalName = this.name;
            this.element = null;
            this.keyElement = null;
            if (this.builder.options.convertFieldsToCamelCase && !(this instanceof d.ExtensionField)) {
                this.name = l.Util.toCamelCase(this.name)
            }
        };
        var B = j.prototype = Object.create(h.prototype);
        B.build = function() {
            this.element = new s(this.type,this.resolvedType,false,this.syntax,this.name);
            if (this.map) {
                this.keyElement = new s(this.keyType,undefined,true,this.syntax,this.name)
            }
            if (this.syntax === "proto3" && !this.repeated && !this.map) {
                this.defaultValue = s.defaultFieldValue(this.type)
            } else {
                if (typeof this.options["default"] !== "undefined") {
                    this.defaultValue = this.verifyValue(this.options["default"])
                }
            }
        }
        ;
        B.verifyValue = function(I, E) {
            E = E || false;
            var F = this;
            function D(K, J) {
                throw Error("Illegal value for " + F.toString(true) + " of type " + F.type.name + ": " + K + " (" + J + ")")
            }
            if (I === null) {
                if (this.required) {
                    D(typeof I, "required")
                }
                if (this.syntax === "proto3" && this.type !== l.TYPES.message) {
                    D(typeof I, "proto3 field without field presence cannot be null")
                }
                return null
            }
            var H;
            if (this.repeated && !E) {
                if (!Array.isArray(I)) {
                    I = [I]
                }
                var G = [];
                for (H = 0; H < I.length; H++) {
                    G.push(this.element.verifyValue(I[H]))
                }
                return G
            }
            if (this.map && !E) {
                if (!(I instanceof l.Map)) {
                    if (!(I instanceof Object)) {
                        D(typeof I, "expected ProtoBuf.Map or raw object for map field")
                    }
                    return new l.Map(this,I)
                } else {
                    return I
                }
            }
            if (!this.repeated && Array.isArray(I)) {
                D(typeof I, "no array expected")
            }
            return this.element.verifyValue(I)
        }
        ;
        B.hasWirePresence = function(E, D) {
            if (this.syntax !== "proto3") {
                return (E !== null)
            }
            if (this.oneof && D[this.oneof.name] === this.name) {
                return true
            }
            switch (this.type) {
            case l.TYPES.int32:
            case l.TYPES.sint32:
            case l.TYPES.sfixed32:
            case l.TYPES.uint32:
            case l.TYPES.fixed32:
                return E !== 0;
            case l.TYPES.int64:
            case l.TYPES.sint64:
            case l.TYPES.sfixed64:
            case l.TYPES.uint64:
            case l.TYPES.fixed64:
                return E.low !== 0 || E.high !== 0;
            case l.TYPES.bool:
                return E;
            case l.TYPES["float"]:
            case l.TYPES["double"]:
                return E !== 0;
            case l.TYPES.string:
                return E.length > 0;
            case l.TYPES.bytes:
                return E.remaining() > 0;
            case l.TYPES["enum"]:
                return E !== 0;
            case l.TYPES.message:
                return E !== null;
            default:
                return true
            }
        }
        ;
        B.encode = function(K, G, L) {
            if (this.type === null || typeof this.type !== "object") {
                throw Error("[INTERNAL] Unresolved type in " + this.toString(true) + ": " + this.type)
            }
            if (K === null || (this.repeated && K.length == 0)) {
                return G
            }
            try {
                if (this.repeated) {
                    var H;
                    if (this.options.packed && l.PACKABLE_WIRE_TYPES.indexOf(this.type.wireType) >= 0) {
                        G.writeVarint32((this.id << 3) | l.WIRE_TYPES.LDELIM);
                        G.ensureCapacity(G.offset += 1);
                        var D = G.offset;
                        for (H = 0; H < K.length; H++) {
                            this.element.encodeValue(this.id, K[H], G)
                        }
                        var I = G.offset - D
                          , F = b.calculateVarint32(I);
                        if (F > 1) {
                            var E = G.slice(D, G.offset);
                            D += F - 1;
                            G.offset = D;
                            G.append(E)
                        }
                        G.writeVarint32(I, D - F)
                    } else {
                        for (H = 0; H < K.length; H++) {
                            G.writeVarint32((this.id << 3) | this.type.wireType),
                            this.element.encodeValue(this.id, K[H], G)
                        }
                    }
                } else {
                    if (this.map) {
                        K.forEach(function(P, N, M) {
                            var O = b.calculateVarint32((1 << 3) | this.keyType.wireType) + this.keyElement.calculateLength(1, N) + b.calculateVarint32((2 << 3) | this.type.wireType) + this.element.calculateLength(2, P);
                            G.writeVarint32((this.id << 3) | l.WIRE_TYPES.LDELIM);
                            G.writeVarint32(O);
                            G.writeVarint32((1 << 3) | this.keyType.wireType);
                            this.keyElement.encodeValue(1, N, G);
                            G.writeVarint32((2 << 3) | this.type.wireType);
                            this.element.encodeValue(2, P, G)
                        }, this)
                    } else {
                        if (this.hasWirePresence(K, L)) {
                            G.writeVarint32((this.id << 3) | this.type.wireType);
                            this.element.encodeValue(this.id, K, G)
                        }
                    }
                }
            } catch (J) {
                throw Error("Illegal value for " + this.toString(true) + ": " + K + " (" + J + ")")
            }
            return G
        }
        ;
        B.calculate = function(G, F) {
            G = this.verifyValue(G);
            if (this.type === null || typeof this.type !== "object") {
                throw Error("[INTERNAL] Unresolved type in " + this.toString(true) + ": " + this.type)
            }
            if (G === null || (this.repeated && G.length == 0)) {
                return 0
            }
            var I = 0;
            try {
                if (this.repeated) {
                    var E, D;
                    if (this.options.packed && l.PACKABLE_WIRE_TYPES.indexOf(this.type.wireType) >= 0) {
                        I += b.calculateVarint32((this.id << 3) | l.WIRE_TYPES.LDELIM);
                        D = 0;
                        for (E = 0; E < G.length; E++) {
                            D += this.element.calculateLength(this.id, G[E])
                        }
                        I += b.calculateVarint32(D);
                        I += D
                    } else {
                        for (E = 0; E < G.length; E++) {
                            I += b.calculateVarint32((this.id << 3) | this.type.wireType),
                            I += this.element.calculateLength(this.id, G[E])
                        }
                    }
                } else {
                    if (this.map) {
                        G.forEach(function(M, K, J) {
                            var L = b.calculateVarint32((1 << 3) | this.keyType.wireType) + this.keyElement.calculateLength(1, K) + b.calculateVarint32((2 << 3) | this.type.wireType) + this.element.calculateLength(2, M);
                            I += b.calculateVarint32((this.id << 3) | l.WIRE_TYPES.LDELIM);
                            I += b.calculateVarint32(L);
                            I += L
                        }, this)
                    } else {
                        if (this.hasWirePresence(G, F)) {
                            I += b.calculateVarint32((this.id << 3) | this.type.wireType);
                            I += this.element.calculateLength(this.id, G)
                        }
                    }
                }
            } catch (H) {
                throw Error("Illegal value for " + this.toString(true) + ": " + G + " (" + H + ")")
            }
            return I
        }
        ;
        B.decode = function(J, E, G) {
            var I, F;
            var M = (!this.map && J == this.type.wireType) || (!G && this.repeated && this.options.packed && J == l.WIRE_TYPES.LDELIM) || (this.map && J == l.WIRE_TYPES.LDELIM);
            if (!M) {
                throw Error("Illegal wire type for field " + this.toString(true) + ": " + J + " (" + this.type.wireType + " expected)")
            }
            if (J == l.WIRE_TYPES.LDELIM && this.repeated && this.options.packed && l.PACKABLE_WIRE_TYPES.indexOf(this.type.wireType) >= 0) {
                if (!G) {
                    F = E.readVarint32();
                    F = E.offset + F;
                    var L = [];
                    while (E.offset < F) {
                        L.push(this.decode(this.type.wireType, E, true))
                    }
                    return L
                }
            }
            if (this.map) {
                var K = s.defaultFieldValue(this.keyType);
                I = s.defaultFieldValue(this.type);
                F = E.readVarint32();
                if (E.remaining() < F) {
                    throw Error("Illegal number of bytes for " + this.toString(true) + ": " + F + " required but got only " + E.remaining())
                }
                var H = E.clone();
                H.limit = H.offset + F;
                E.offset += F;
                while (H.remaining() > 0) {
                    var N = H.readVarint32();
                    J = N & 7;
                    var D = N >>> 3;
                    if (D === 1) {
                        K = this.keyElement.decode(H, J, D)
                    } else {
                        if (D === 2) {
                            I = this.element.decode(H, J, D)
                        } else {
                            throw Error("Unexpected tag in map field key/value submessage")
                        }
                    }
                }
                return [K, I]
            }
            return this.element.decode(E, J, this.id)
        }
        ;
        g.Message.Field = j;
        var t = function(D, H, I, G, F, J, E) {
            j.call(this, D, H, I, null, G, F, J, E);
            this.extension
        };
        t.prototype = Object.create(j.prototype);
        g.Message.ExtensionField = t;
        var v = function(D, F, E) {
            h.call(this, D, F, E);
            this.fields = []
        };
        g.Message.OneOf = v;
        var q = function(E, H, G, F, D) {
            p.call(this, E, H, G, F, D);
            this.className = "Enum";
            this.object = null
        };
        q.getName = function(D, H) {
            var G = Object.keys(D);
            for (var F = 0, E; F < G.length; ++F) {
                if (D[E = G[F]] === H) {
                    return E
                }
            }
            return null
        }
        ;
        var i = q.prototype = Object.create(p.prototype);
        i.build = function(D) {
            if (this.object && !D) {
                return this.object
            }
            var G = new l.Builder.Enum()
              , F = this.getChildren(q.Value);
            for (var H = 0, E = F.length; H < E; ++H) {
                G[F[H]["name"]] = F[H]["id"]
            }
            if (Object.defineProperty) {
                Object.defineProperty(G, "$options", {
                    value: this.buildOpt(),
                    enumerable: false
                })
            }
            return this.object = G
        }
        ;
        g.Enum = q;
        var z = function(D, F, E, G) {
            h.call(this, D, F, E);
            this.className = "Enum.Value";
            this.id = G
        };
        z.prototype = Object.create(h.prototype);
        g.Enum.Value = z;
        var n = function(D, F, E, G) {
            h.call(this, D, F, E);
            this.field = G
        };
        n.prototype = Object.create(h.prototype);
        g.Extension = n;
        var o = function(E, D, G, F) {
            p.call(this, E, D, G, F);
            this.className = "Service";
            this.clazz = null
        };
        var y = o.prototype = Object.create(p.prototype);
        y.build = function(D) {
            if (this.clazz && !D) {
                return this.clazz
            }
            return this.clazz = (function(L, G) {
                var F = function(O) {
                    L.Builder.Service.call(this);
                    this.rpcImpl = O || function(P, Q, R) {
                        setTimeout(R.bind(this, Error("Not implemented, see: https://github.com/dcodeIO/ProtoBuf.js/wiki/Services")), 0)
                    }
                };
                var M = F.prototype = Object.create(L.Builder.Service.prototype);
                var J = G.getChildren(L.Reflect.Service.RPCMethod);
                for (var H = 0; H < J.length; H++) {
                    (function(O) {
                        M[O.name] = function(Q, R) {
                            try {
                                try {
                                    Q = O.resolvedRequestType.clazz.decode(b.wrap(Q))
                                } catch (P) {
                                    if (!(P instanceof TypeError)) {
                                        throw P
                                    }
                                }
                                if (Q === null || typeof Q !== "object") {
                                    throw Error("Illegal arguments")
                                }
                                if (!(Q instanceof O.resolvedRequestType.clazz)) {
                                    Q = new O.resolvedRequestType.clazz(Q)
                                }
                                this.rpcImpl(O.fqn(), Q, function(T, S) {
                                    if (T) {
                                        R(T);
                                        return
                                    }
                                    if (S === null) {
                                        S = ""
                                    }
                                    try {
                                        S = O.resolvedResponseType.clazz.decode(S)
                                    } catch (U) {}
                                    if (!S || !(S instanceof O.resolvedResponseType.clazz)) {
                                        R(Error("Illegal response type received in service method " + G.name + "#" + O.name));
                                        return
                                    }
                                    R(null, S)
                                })
                            } catch (P) {
                                setTimeout(R.bind(this, P), 0)
                            }
                        }
                        ;
                        F[O.name] = function(P, Q, R) {
                            new F(P)[O.name](Q, R)
                        }
                        ;
                        if (Object.defineProperty) {
                            Object.defineProperty(F[O.name], "$options", {
                                value: O.buildOpt()
                            }),
                            Object.defineProperty(M[O.name], "$options", {
                                value: F[O.name]["$options"]
                            })
                        }
                    }
                    )(J[H])
                }
                var E;
                var I;
                var N;
                var K;
                if (Object.defineProperty) {
                    Object.defineProperty(F, "$options", {
                        value: G.buildOpt()
                    }),
                    Object.defineProperty(M, "$options", {
                        value: F["$options"]
                    }),
                    Object.defineProperty(F, "$type", {
                        value: G
                    }),
                    Object.defineProperty(M, "$type", {
                        value: G
                    })
                }
                return F
            }
            )(l, this)
        }
        ;
        g.Service = o;
        var e = function(D, G, F, E) {
            h.call(this, D, G, F);
            this.className = "Service.Method";
            this.options = E || {}
        };
        var m = e.prototype = Object.create(h.prototype);
        m.buildOpt = u.buildOpt;
        g.Service.Method = e;
        var r = function(F, K, I, J, E, H, D, G) {
            e.call(this, F, K, I, G);
            this.className = "Service.RPCMethod";
            this.requestName = J;
            this.responseName = E;
            this.requestStream = H;
            this.responseStream = D;
            this.resolvedRequestType = null;
            this.resolvedResponseType = null
        };
        r.prototype = Object.create(e.prototype);
        g.Service.RPCMethod = r;
        return g
    }
    )(c);
    c.Builder = (function(g, f, i) {
        var h = function(j) {
            this.ns = new i.Namespace(this,null,"");
            this.ptr = this.ns;
            this.resolved = false;
            this.result = null;
            this.files = {};
            this.importRoot = null;
            this.options = j || {}
        };
        var d = h.prototype;
        h.isMessage = function(j) {
            if (typeof j.name !== "string") {
                return false
            }
            if (typeof j.values !== "undefined" || typeof j.rpc !== "undefined") {
                return false
            }
            return true
        }
        ;
        h.isMessageField = function(j) {
            if (typeof j.rule !== "string" || typeof j.name !== "string" || typeof j.type !== "string" || typeof j.id === "undefined") {
                return false
            }
            return true
        }
        ;
        h.isEnum = function(j) {
            if (typeof j.name !== "string") {
                return false
            }
            if (typeof j.values === "undefined" || !Array.isArray(j.values) || j.values.length === 0) {
                return false
            }
            return true
        }
        ;
        h.isService = function(j) {
            if (typeof j.name !== "string" || typeof j.rpc !== "object" || !j.rpc) {
                return false
            }
            return true
        }
        ;
        h.isExtend = function(j) {
            if (typeof j.ref !== "string") {
                return false
            }
            return true
        }
        ;
        d.reset = function() {
            this.ptr = this.ns;
            return this
        }
        ;
        d.define = function(j) {
            if (typeof j !== "string" || !f.TYPEREF.test(j)) {
                throw Error("illegal namespace: " + j)
            }
            j.split(".").forEach(function(k) {
                var l = this.ptr.getChild(k);
                if (l === null) {
                    this.ptr.addChild(l = new i.Namespace(this,this.ptr,k))
                }
                this.ptr = l
            }, this);
            return this
        }
        ;
        d.create = function(k) {
            if (!k) {
                return this
            }
            if (!Array.isArray(k)) {
                k = [k]
            } else {
                if (k.length === 0) {
                    return this
                }
                k = k.slice()
            }
            var j = [k];
            while (j.length > 0) {
                k = j.pop();
                if (!Array.isArray(k)) {
                    throw Error("not a valid namespace: " + JSON.stringify(k))
                }
                while (k.length > 0) {
                    var n = k.shift();
                    if (h.isMessage(n)) {
                        var o = new i.Message(this,this.ptr,n.name,n.options,n.isGroup,n.syntax);
                        var m = {};
                        if (n.oneofs) {
                            Object.keys(n.oneofs).forEach(function(p) {
                                o.addChild(m[p] = new i.Message.OneOf(this,o,p))
                            }, this)
                        }
                        if (n.fields) {
                            n.fields.forEach(function(p) {
                                if (o.getChild(p.id | 0) !== null) {
                                    throw Error("duplicate or invalid field id in " + o.name + ": " + p.id)
                                }
                                if (p.options && typeof p.options !== "object") {
                                    throw Error("illegal field options in " + o.name + "#" + p.name)
                                }
                                var q = null;
                                if (typeof p.oneof === "string" && !(q = m[p.oneof])) {
                                    throw Error("illegal oneof in " + o.name + "#" + p.name + ": " + p.oneof)
                                }
                                p = new i.Message.Field(this,o,p.rule,p.keytype,p.type,p.name,p.id,p.options,q,n.syntax);
                                if (q) {
                                    q.fields.push(p)
                                }
                                o.addChild(p)
                            }, this)
                        }
                        var l = [];
                        if (n.enums) {
                            n.enums.forEach(function(p) {
                                l.push(p)
                            })
                        }
                        if (n.messages) {
                            n.messages.forEach(function(p) {
                                l.push(p)
                            })
                        }
                        if (n.services) {
                            n.services.forEach(function(p) {
                                l.push(p)
                            })
                        }
                        if (n.extensions) {
                            if (typeof n.extensions[0] === "number") {
                                o.extensions = [n.extensions]
                            } else {
                                o.extensions = n.extensions
                            }
                        }
                        this.ptr.addChild(o);
                        if (l.length > 0) {
                            j.push(k);
                            k = l;
                            l = null;
                            this.ptr = o;
                            o = null;
                            continue
                        }
                        l = null
                    } else {
                        if (h.isEnum(n)) {
                            o = new i.Enum(this,this.ptr,n.name,n.options,n.syntax);
                            n.values.forEach(function(p) {
                                o.addChild(new i.Enum.Value(this,o,p.name,p.id))
                            }, this);
                            this.ptr.addChild(o)
                        } else {
                            if (h.isService(n)) {
                                o = new i.Service(this,this.ptr,n.name,n.options);
                                Object.keys(n.rpc).forEach(function(q) {
                                    var p = n.rpc[q];
                                    o.addChild(new i.Service.RPCMethod(this,o,q,p.request,p.response,!!p.request_stream,!!p.response_stream,p.options))
                                }, this);
                                this.ptr.addChild(o)
                            } else {
                                if (h.isExtend(n)) {
                                    o = this.ptr.resolve(n.ref, true);
                                    if (o) {
                                        n.fields.forEach(function(q) {
                                            if (o.getChild(q.id | 0) !== null) {
                                                throw Error("duplicate extended field id in " + o.name + ": " + q.id)
                                            }
                                            if (o.extensions) {
                                                var s = false;
                                                o.extensions.forEach(function(u) {
                                                    if (q.id >= u[0] && q.id <= u[1]) {
                                                        s = true
                                                    }
                                                });
                                                if (!s) {
                                                    throw Error("illegal extended field id in " + o.name + ": " + q.id + " (not within valid ranges)")
                                                }
                                            }
                                            var p = q.name;
                                            if (this.options.convertFieldsToCamelCase) {
                                                p = g.Util.toCamelCase(p)
                                            }
                                            var t = new i.Message.ExtensionField(this,o,q.rule,q.type,this.ptr.fqn() + "." + p,q.id,q.options);
                                            var r = new i.Extension(this,this.ptr,q.name,t);
                                            t.extension = r;
                                            this.ptr.addChild(r);
                                            o.addChild(t)
                                        }, this)
                                    } else {
                                        if (!/\.?google\.protobuf\./.test(n.ref)) {
                                            throw Error("extended message " + n.ref + " is not defined")
                                        }
                                    }
                                } else {
                                    throw Error("not a valid definition: " + JSON.stringify(n))
                                }
                            }
                        }
                    }
                    n = null;
                    o = null
                }
                k = null;
                this.ptr = this.ptr.parent
            }
            this.resolved = false;
            this.result = null;
            return this
        }
        ;
        function e(j) {
            if (j.messages) {
                j.messages.forEach(function(k) {
                    k.syntax = j.syntax;
                    e(k)
                })
            }
            if (j.enums) {
                j.enums.forEach(function(k) {
                    k.syntax = j.syntax
                })
            }
        }
        d["import"] = function(t, j) {
            var l = "/";
            if (typeof j === "string") {
                if (g.Util.IS_NODE) {
                    j = require("path")["resolve"](j)
                }
                if (this.files[j] === true) {
                    return this.reset()
                }
                this.files[j] = true
            } else {
                if (typeof j === "object") {
                    var r = j.root;
                    if (g.Util.IS_NODE) {
                        r = require("path")["resolve"](r)
                    }
                    if (r.indexOf("\\") >= 0 || j.file.indexOf("\\") >= 0) {
                        l = "\\"
                    }
                    var m = r + l + j.file;
                    if (this.files[m] === true) {
                        return this.reset()
                    }
                    this.files[m] = true
                }
            }
            if (t.imports && t.imports.length > 0) {
                var o, q = false;
                if (typeof j === "object") {
                    this.importRoot = j.root;
                    q = true;
                    o = this.importRoot;
                    j = j.file;
                    if (o.indexOf("\\") >= 0 || j.indexOf("\\") >= 0) {
                        l = "\\"
                    }
                } else {
                    if (typeof j === "string") {
                        if (this.importRoot) {
                            o = this.importRoot
                        } else {
                            if (j.indexOf("/") >= 0) {
                                o = j.replace(/\/[^\/]*$/, "");
                                if (o === "") {
                                    o = "/"
                                }
                            } else {
                                if (j.indexOf("\\") >= 0) {
                                    o = j.replace(/\\[^\\]*$/, "");
                                    l = "\\"
                                } else {
                                    o = "."
                                }
                            }
                        }
                    } else {
                        o = null
                    }
                }
                for (var p = 0; p < t.imports.length; p++) {
                    if (typeof t.imports[p] === "string") {
                        if (!o) {
                            throw Error("cannot determine import root")
                        }
                        var s = t.imports[p];
                        if (s === "google/protobuf/descriptor.proto") {
                            continue
                        }
                        s = o + l + s;
                        if (this.files[s] === true) {
                            continue
                        }
                        if (/\.proto$/i.test(s) && !g.DotProto) {
                            s = s.replace(/\.proto$/, ".json")
                        }
                        var n = g.Util.fetch(s);
                        if (n === null) {
                            throw Error("failed to import '" + s + "' in '" + j + "': file not found")
                        }
                        if (/\.json$/i.test(s)) {
                            this["import"](JSON.parse(n + ""), s)
                        } else {
                            this["import"](g.DotProto.Parser.parse(n), s)
                        }
                    } else {
                        if (!j) {
                            this["import"](t.imports[p])
                        } else {
                            if (/\.(\w+)$/.test(j)) {
                                this["import"](t.imports[p], j.replace(/^(.+)\.(\w+)$/, function(v, u, w) {
                                    return u + "_import" + p + "." + w
                                }))
                            } else {
                                this["import"](t.imports[p], j + "_import" + p)
                            }
                        }
                    }
                }
                if (q) {
                    this.importRoot = null
                }
            }
            if (t["package"]) {
                this.define(t["package"])
            }
            if (t.syntax) {
                e(t)
            }
            var k = this.ptr;
            if (t.options) {
                Object.keys(t.options).forEach(function(u) {
                    k.options[u] = t.options[u]
                })
            }
            if (t.messages) {
                this.create(t.messages),
                this.ptr = k
            }
            if (t.enums) {
                this.create(t.enums),
                this.ptr = k
            }
            if (t.services) {
                this.create(t.services),
                this.ptr = k
            }
            if (t["extends"]) {
                this.create(t["extends"])
            }
            return this.reset()
        }
        ;
        d.resolveAll = function() {
            var j;
            if (this.ptr == null || typeof this.ptr.type === "object") {
                return this
            }
            if (this.ptr instanceof i.Namespace) {
                this.ptr.children.forEach(function(k) {
                    this.ptr = k;
                    this.resolveAll()
                }, this)
            } else {
                if (this.ptr instanceof i.Message.Field) {
                    if (!f.TYPE.test(this.ptr.type)) {
                        if (!f.TYPEREF.test(this.ptr.type)) {
                            throw Error("illegal type reference in " + this.ptr.toString(true) + ": " + this.ptr.type)
                        }
                        j = (this.ptr instanceof i.Message.ExtensionField ? this.ptr.extension.parent : this.ptr.parent).resolve(this.ptr.type, true);
                        if (!j) {
                            throw Error("unresolvable type reference in " + this.ptr.toString(true) + ": " + this.ptr.type)
                        }
                        this.ptr.resolvedType = j;
                        if (j instanceof i.Enum) {
                            this.ptr.type = g.TYPES["enum"];
                            if (this.ptr.syntax === "proto3" && j.syntax !== "proto3") {
                                throw Error("proto3 message cannot reference proto2 enum")
                            }
                        } else {
                            if (j instanceof i.Message) {
                                this.ptr.type = j.isGroup ? g.TYPES.group : g.TYPES.message
                            } else {
                                throw Error("illegal type reference in " + this.ptr.toString(true) + ": " + this.ptr.type)
                            }
                        }
                    } else {
                        this.ptr.type = g.TYPES[this.ptr.type]
                    }
                    if (this.ptr.map) {
                        if (!f.TYPE.test(this.ptr.keyType)) {
                            throw Error("illegal key type for map field in " + this.ptr.toString(true) + ": " + this.ptr.keyType)
                        }
                        this.ptr.keyType = g.TYPES[this.ptr.keyType]
                    }
                } else {
                    if (this.ptr instanceof g.Reflect.Service.Method) {
                        if (this.ptr instanceof g.Reflect.Service.RPCMethod) {
                            j = this.ptr.parent.resolve(this.ptr.requestName, true);
                            if (!j || !(j instanceof g.Reflect.Message)) {
                                throw Error("Illegal type reference in " + this.ptr.toString(true) + ": " + this.ptr.requestName)
                            }
                            this.ptr.resolvedRequestType = j;
                            j = this.ptr.parent.resolve(this.ptr.responseName, true);
                            if (!j || !(j instanceof g.Reflect.Message)) {
                                throw Error("Illegal type reference in " + this.ptr.toString(true) + ": " + this.ptr.responseName)
                            }
                            this.ptr.resolvedResponseType = j
                        } else {
                            throw Error("illegal service type in " + this.ptr.toString(true))
                        }
                    } else {
                        if (!(this.ptr instanceof g.Reflect.Message.OneOf) && !(this.ptr instanceof g.Reflect.Extension) && !(this.ptr instanceof g.Reflect.Enum.Value)) {
                            throw Error("illegal object in namespace: " + typeof (this.ptr) + ": " + this.ptr)
                        }
                    }
                }
            }
            return this.reset()
        }
        ;
        d.build = function(l) {
            this.reset();
            if (!this.resolved) {
                this.resolveAll(),
                this.resolved = true,
                this.result = null
            }
            if (this.result === null) {
                this.result = this.ns.build()
            }
            if (!l) {
                return this.result
            }
            var j = typeof l === "string" ? l.split(".") : l
              , m = this.result;
            for (var k = 0; k < j.length; k++) {
                if (m[j[k]]) {
                    m = m[j[k]]
                } else {
                    m = null;
                    break
                }
            }
            return m
        }
        ;
        d.lookup = function(k, j) {
            return k ? this.ns.resolve(k, j) : this.ns
        }
        ;
        d.toString = function() {
            return "Builder"
        }
        ;
        h.Message = function() {}
        ;
        h.Enum = function() {}
        ;
        h.Service = function() {}
        ;
        return h
    }
    )(c, c.Lang, c.Reflect);
    c.Map = (function(e, h) {
        var d = function(n, m) {
            if (!n.map) {
                throw Error("field is not a map")
            }
            this.field = n;
            this.keyElem = new h.Element(n.keyType,null,true,n.syntax);
            this.valueElem = new h.Element(n.type,n.resolvedType,false,n.syntax);
            this.map = {};
            Object.defineProperty(this, "size", {
                get: function() {
                    return Object.keys(this.map).length
                }
            });
            if (m) {
                var l = Object.keys(m);
                for (var k = 0; k < l.length; k++) {
                    var j = this.keyElem.valueFromString(l[k]);
                    var o = this.valueElem.verifyValue(m[l[k]]);
                    this.map[this.keyElem.valueToString(j)] = {
                        key: j,
                        value: o
                    }
                }
            }
        };
        var f = d.prototype;
        function g(j) {
            var i = 0;
            return {
                next: function() {
                    if (i < j.length) {
                        return {
                            done: false,
                            value: j[i++]
                        }
                    }
                    return {
                        done: true
                    }
                }
            }
        }
        f.clear = function() {
            this.map = {}
        }
        ;
        f["delete"] = function(j) {
            var k = this.keyElem.valueToString(this.keyElem.verifyValue(j));
            var i = k in this.map;
            delete this.map[k];
            return i
        }
        ;
        f.entries = function() {
            var j = [];
            var m = Object.keys(this.map);
            for (var k = 0, l; k < m.length; k++) {
                j.push([(l = this.map[m[k]]).key, l.value])
            }
            return g(j)
        }
        ;
        f.keys = function() {
            var k = [];
            var l = Object.keys(this.map);
            for (var j = 0; j < l.length; j++) {
                k.push(this.map[l[j]].key)
            }
            return g(k)
        }
        ;
        f.values = function() {
            var j = [];
            var l = Object.keys(this.map);
            for (var k = 0; k < l.length; k++) {
                j.push(this.map[l[k]].value)
            }
            return g(j)
        }
        ;
        f.forEach = function(j, k) {
            var n = Object.keys(this.map);
            for (var l = 0, m; l < n.length; l++) {
                j.call(k, (m = this.map[n[l]]).value, m.key, this)
            }
        }
        ;
        f.set = function(i, k) {
            var l = this.keyElem.verifyValue(i);
            var j = this.valueElem.verifyValue(k);
            this.map[this.keyElem.valueToString(l)] = {
                key: l,
                value: j
            };
            return this
        }
        ;
        f.get = function(i) {
            var j = this.keyElem.valueToString(this.keyElem.verifyValue(i));
            if (!(j in this.map)) {
                return undefined
            }
            return this.map[j].value
        }
        ;
        f.has = function(i) {
            var j = this.keyElem.valueToString(this.keyElem.verifyValue(i));
            return (j in this.map)
        }
        ;
        return d
    }
    )(c, c.Reflect);
    c.loadProto = function(f, e, d) {
        if (typeof e === "string" || (e && typeof e.file === "string" && typeof e.root === "string")) {
            d = e,
            e = undefined
        }
        return c.loadJson(c.DotProto.Parser.parse(f), e, d)
    }
    ;
    c.protoFromString = c.loadProto;
    c.loadProtoFile = function(e, g, d) {
        if (g && typeof g === "object") {
            d = g,
            g = null
        } else {
            if (!g || typeof g !== "function") {
                g = null
            }
        }
        if (g) {
            return c.Util.fetch(typeof e === "string" ? e : e.root + "/" + e.file, function(h) {
                if (h === null) {
                    g(Error("Failed to fetch file"));
                    return
                }
                try {
                    g(null, c.loadProto(h, d, e))
                } catch (i) {
                    g(i)
                }
            })
        }
        var f = c.Util.fetch(typeof e === "object" ? e.root + "/" + e.file : e);
        return f === null ? null : c.loadProto(f, d, e)
    }
    ;
    c.protoFromFile = c.loadProtoFile;
    c.newBuilder = function(d) {
        d = d || {};
        if (typeof d.convertFieldsToCamelCase === "undefined") {
            d.convertFieldsToCamelCase = c.convertFieldsToCamelCase
        }
        if (typeof d.populateAccessors === "undefined") {
            d.populateAccessors = c.populateAccessors
        }
        return new c.Builder(d)
    }
    ;
    c.loadJson = function(f, e, d) {
        if (typeof e === "string" || (e && typeof e.file === "string" && typeof e.root === "string")) {
            d = e,
            e = null
        }
        if (!e || typeof e !== "object") {
            e = c.newBuilder()
        }
        if (typeof f === "string") {
            f = JSON.parse(f)
        }
        e["import"](f, d);
        e.resolveAll();
        return e
    }
    ;
    c.loadJsonFile = function(e, g, d) {
        if (g && typeof g === "object") {
            d = g,
            g = null
        } else {
            if (!g || typeof g !== "function") {
                g = null
            }
        }
        if (g) {
            return c.Util.fetch(typeof e === "string" ? e : e.root + "/" + e.file, function(h) {
                if (h === null) {
                    g(Error("Failed to fetch file"));
                    return
                }
                try {
                    g(null, c.loadJson(JSON.parse(h), d, e))
                } catch (i) {
                    g(i)
                }
            })
        }
        var f = c.Util.fetch(typeof e === "object" ? e.root + "/" + e.file : e);
        return f === null ? null : c.loadJson(JSON.parse(f), d, e)
    }
    ;
    return c
});
window.__PROTO_FILE_VAR__ = 'option java_package = "cn.techwolf.boss.chat";option java_outer_classname = "ChatProtocol";message TechwolfUser {required int64 uid = 1;optional string name = 2;optional string avatar = 3;optional string company = 4;optional int32 headImg = 5;optional int32 certification = 6;optional int32 source = 7;}message TechwolfSound {optional int64 sid = 1;optional string url = 2;optional int32 duration = 3;optional int32 templateId = 4;}message TechwolfVideo {required int32 type = 1;required int32 status = 2;optional int32 duration = 3;optional string text = 4;}message TechwolfInterview {required int32 condition = 1;required string text = 2;optional string url = 3;optional string extend = 4;}message TechwolfImageInfo {required string url = 1;required int32 width = 2;required int32 height = 3;}message TechwolfImage {optional int64 iid = 1;optional TechwolfImageInfo tinyImage = 2;optional TechwolfImageInfo originImage = 3;}message TechwolfAction {required int32 aid = 1;optional string extend = 2;}message TechwolfArticle {required string title = 1;required string description = 2;required string picUrl = 3;required string url = 4;optional int32 templateId = 5;optional string bottomText = 6;optional int64 timeout = 7;optional string statisticParameters = 8;repeated TechwolfSlice highlightParts = 9;repeated TechwolfSlice dimParts = 10;optional string subTitle = 11;optional string extend = 12;}message TechwolfNotify {required string text = 1;optional string url = 2;optional string title = 3;}message TechwolfButton {required string text = 1;optional string url = 2;optional int32 templateId = 3;}message TechwolfDialog {required string text = 1;repeated TechwolfButton buttons = 2;required bool operated = 3;optional bool clickMore = 4;optional int32 type = 5;optional string backgroundUrl = 6;optional int64 timeout = 7;optional string statisticParameters = 8;optional string title = 9;optional string url = 10;optional int32 selectedIndex = 11;optional string extend = 12;optional string content = 13;}message TechwolfJobDesc {required string title = 1;required string company = 2;required string salary = 3;required string url = 4;required int64 jobId = 5;optional string positionCategory = 6;optional string experience = 7;optional string education = 8;optional string city = 9;optional string bossTitle = 10;optional TechwolfUser boss = 11;optional string lid = 12;optional string stage = 13;optional string bottomText = 14;optional string jobLabel = 15;optional int32 iconFlag = 16;optional string content = 17;repeated string labels = 18;optional int64 expectId = 19;optional string expectPosition = 20;optional string expectSalary = 21;optional string partTimeDesc = 22;optional TechwolfUser geek = 23;optional string latlon = 24;optional string distance = 25;}message TechwolfResume {required TechwolfUser user = 1;optional string description = 2;optional string city = 3;optional string position = 4;repeated string keywords = 5;optional int64 expectId = 6;optional string lid = 7;optional int32 gender = 8;optional string salary = 9;optional string workYear = 10;optional string content1 = 11;optional string content2 = 12;optional string education = 13;optional string age = 14;repeated string labels = 15;repeated UserExperience experiences = 16;optional string positionCategory = 17;optional string jobSalary = 18;optional string bottomText = 19;optional string applyStatus = 20;optional int64 jobId = 21;optional string content3 = 22;optional string securityId = 23;optional TechwolfUser boss = 24;optional string brandName = 25;}message TechwolfHyperLink {required string text = 1;required string url = 2;required int32 hyperLinkType = 3;optional string extraJson=4;}message TechwolfMessageBody {required int32 type = 1;required int32 templateId = 2;optional string headTitle = 11;optional string text = 3;optional TechwolfSound sound = 4;optional TechwolfImage image = 5;optional TechwolfAction action = 6;repeated TechwolfArticle articles = 7;optional TechwolfNotify notify = 8;optional TechwolfDialog dialog = 9;optional TechwolfJobDesc jobDesc = 10;optional TechwolfResume resume = 12;optional TechwolfRedEnvelope redEnvelope = 13;optional TechwolfOrderDetail orderDetail = 14;optional TechwolfHyperLink hyperLink = 15;optional TechwolfVideo video = 16;optional TechwolfInterview interview = 17;optional TechwolfJobShare jobShare = 18;optional TechwolfResumeShare resumeShare = 19;optional AtInfo atInfo = 20;optional TechwolfSticker sticker = 21;optional TechwolfChatShare chatShare = 22;optional TechwolfInterviewShare interviewShare = 23;optional TechwolfListCard listCard = 24;optional TechwolfStarRate starRate = 25;optional TechwolfFrame frame = 26;optional TechwolfMultiImage multiImage = 27;optional string extend = 28;}message TechwolfMessage {required TechwolfUser from = 1;required TechwolfUser to = 2;required int32 type = 3;optional int64 mid = 4;optional int64 time = 5;required TechwolfMessageBody body = 6;optional bool offline = 7;optional bool received = 8;optional string pushText = 9;optional int64 taskId = 10;optional int64 cmid = 11;optional int32 status = 12;optional int32 uncount = 13;optional int32 pushSound = 14;optional int32 flag = 15;optional bytes encryptedBody = 16;optional string bizId = 17;optional int32 bizType = 18;optional string securityId = 19;}message TechwolfClientInfo {optional string version = 1;optional string system = 2;optional string systemVersion = 3;optional string model = 4;optional string uniqid = 5;optional string network = 6;optional int32 appid = 7;optional string platform = 8;optional string channel = 9;optional string ssid = 10;optional string bssid = 11;optional double longitude = 12;optional double latitude = 13;}message TechwolfClientTime {optional int64 startTime = 1;optional int64 resumeTime = 2;}message TechwolfPresence {required int32 type = 1;required int32 uid = 2;optional TechwolfClientInfo clientInfo = 3;optional TechwolfClientTime clientTime = 4;optional int64 lastMessageId = 5;optional int64 lastGroupMessageId = 6;optional int64 userId = 7;}message TechwolfKVEntry {required string key = 1;required string value = 2;}message TechwolfIq {required int64 qid = 1;required string query = 2;repeated TechwolfKVEntry params = 3;}message TechwolfIqResponse {required int64 qid = 1;required string query = 2;repeated TechwolfKVEntry results = 3;}message TechwolfMessageSync {required int64 clientMid = 1;required int64 serverMid = 2;}message TechwolfMessageRead {required int64 userId = 1;required int64 messageId = 2;required int64 readTime = 3;optional bool sync = 4 [default = false];optional int32 userSource = 5;}message TechwolfChatProtocol {required int32 type = 1;optional string version = 2;repeated TechwolfMessage messages = 3;optional TechwolfPresence presence = 4;optional TechwolfIq iq = 5;optional TechwolfIqResponse iqResponse = 6;repeated TechwolfMessageSync messageSync = 7;repeated TechwolfMessageRead messageRead = 8;optional TechwolfDataSync dataSync = 9;optional int32 domain = 10;}message TechwolfRedEnvelope {required int64 redId = 1;required string redText = 2;required string redTitle = 3;required string clickUrl = 4;}message TechwolfOrderDetail {required string title = 1;required string subTitle = 2;optional string url = 3;repeated TechwolfOrderDetailEntry orderDetailEntryList =  4;}message TechwolfOrderDetailItem {required string name = 1;required int32 templateId = 2;}message TechwolfOrderDetailEntry {required TechwolfOrderDetailItem key = 1;required TechwolfOrderDetailItem value = 2;}message TechwolfUserSync {required int64 uid = 1;required int32 identity = 2;optional string extraJson = 3;optional int32 userSource = 4;}message TechwolfDataSync {required int32 type = 1;optional TechwolfUserSync userSync = 2;optional TechwolfGroupSync groupSync = 3;}message TechwolfSlice {required int32 startIndex = 1;required int32 endIndex = 2;}message UserExperience {required string organization = 1;required string occupation = 2;optional string startDate = 3;optional string endDate = 4;required int32 type = 5;}message TechwolfJobShare {required TechwolfUser user = 1;required int64 jobId = 2;required string position = 3;required string salary = 4;optional string location = 5;required string company = 6;optional string stage = 7;optional string experience = 8;optional string education = 9;optional string url = 10;optional string lid = 11;optional string price = 12;optional string description = 13;}message TechwolfResumeShare {required TechwolfUser user = 1;required int64 expectId = 2;required string position = 3;required string salary = 4;optional string location = 5;optional string applyStatus = 6;optional string age = 7;optional string experience = 8;optional string education = 9;optional string url = 10;optional string lid = 11;optional int32 gender = 12;optional bool blurred = 13;optional int32 source = 14;}message AtInfo {required int32 flag = 1;repeated int64 uids = 2;}message TechwolfGroupSync {required int64 gid = 1;optional int32 version = 2;optional string encGid = 3;}message TechwolfSticker {required int64 sid = 1;optional int64 packId = 2;optional TechwolfImage image = 3;optional string format = 4;optional string name = 5;}message TechwolfChatShare {required int64 shareId = 1;required string title = 2;repeated string records = 3;optional string bottomText = 4;optional string url = 5;required TechwolfUser from = 6;required TechwolfUser to = 7;required TechwolfUser user = 8;}message TechwolfInterviewShare {required int64 interviewId = 1;required TechwolfUser user = 2;required string title = 3;required string bottomText = 4;optional string url = 5;optional string interviewTime = 6;optional string interviewAddress = 7;optional string jobName = 8;}message TechwolfListItem {optional string title = 1;optional int32 icon = 2;}message TechwolfListCard {optional string title = 1;repeated TechwolfListItem items = 2;optional int32 pageSize = 3;}message TechwolfStar {required int64 starId = 1;optional string starDesc = 2;repeated TechwolfListItem options = 3;}message TechwolfStarRate {optional string title = 1;repeated TechwolfStar stars = 2;required int32 rateStatus = 3;optional TechwolfStar rateStar = 4;optional TechwolfButton submitButton = 5;}message TechwolfFrame {required string href = 1;}message TechwolfMultiImage {repeated TechwolfImageInfo images = 1;}';
