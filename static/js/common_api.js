/**
 * Created by yuanyifan on 2017/7/25.
 */
function leave_point(value, productor) {
    return Math.round(value * productor) / productor
}

/**
 *
 *  Javascript sprintf
 *  http://www.webtoolkit.info/
 *
 *
 **/
sprintfWrapper = {
    init: function () {
        if (typeof arguments == "undefined") {
            return null;
        }
        if (arguments.length < 1) {
            return null;
        }
        if (typeof arguments[0] != "string") {
            return null;
        }
        if (typeof RegExp == "undefined") {
            return null;
        }
        var string = arguments[0];
        var exp = new RegExp(/(%([%]|(\-)?(\+|\x20)?(0)?(\d+)?(\.(\d)?)?([bcdfosxX])))/g);
        var matches = new Array();
        var strings = new Array();
        var convCount = 0;
        var stringPosStart = 0;
        var stringPosEnd = 0;
        var matchPosEnd = 0;
        var newString = '';
        var match = null;
        while (match = exp.exec(string)) {
            if (match[9]) {
                convCount += 1;
            }
            stringPosStart = matchPosEnd;
            stringPosEnd = exp.lastIndex - match[0].length;
            strings[strings.length] = string.substring(stringPosStart, stringPosEnd);
            matchPosEnd = exp.lastIndex;
            matches[matches.length] = {
                match: match[0],
                left: match[3] ? true : false,
                sign: match[4] || '',
                pad: match[5] || ' ',
                min: match[6] || 0,
                precision: match[8],
                code: match[9] || '%',
                negative: parseInt(arguments[convCount]) < 0 ? true : false,
                argument: String(arguments[convCount])
            };
        }
        strings[strings.length] = string.substring(matchPosEnd);
        if (matches.length == 0) {
            return string;
        }
        if ((arguments.length - 1) < convCount) {
            return null;
        }
        var code = null;
        var match = null;
        var i = null;
        for (i = 0; i < matches.length; i++) {
            if (matches[i].code == '%') {
                substitution = '%'
            }
            else if (matches[i].code == 'b') {
                matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(2));
                substitution = sprintfWrapper.convert(matches[i], true);
            }
            else if (matches[i].code == 'c') {
                matches[i].argument = String(String.fromCharCode(parseInt(Math.abs(parseInt(matches[i].argument)))));
                substitution = sprintfWrapper.convert(matches[i], true);
            }
            else if (matches[i].code == 'd') {
                matches[i].argument = String(Math.abs(parseInt(matches[i].argument)));
                substitution = sprintfWrapper.convert(matches[i]);
            }
            else if (matches[i].code == 'f') {
                matches[i].argument = String(Math.abs(parseFloat(matches[i].argument)).toFixed(matches[i].precision ? matches[i].precision : 6));
                substitution = sprintfWrapper.convert(matches[i]);
            }
            else if (matches[i].code == 'o') {
                matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(8));
                substitution = sprintfWrapper.convert(matches[i]);
            }
            else if (matches[i].code == 's') {
                matches[i].argument = matches[i].argument.substring(0, matches[i].precision ? matches[i].precision : matches[i].argument.length)
                substitution = sprintfWrapper.convert(matches[i], true);
            }
            else if (matches[i].code == 'x') {
                matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(16));
                substitution = sprintfWrapper.convert(matches[i]);
            }
            else if (matches[i].code == 'X') {
                matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(16));
                substitution = sprintfWrapper.convert(matches[i]).toUpperCase();
            }
            else {
                substitution = matches[i].match;
            }
            newString += strings[i];
            newString += substitution;
        }
        newString += strings[i];
        return newString;
    },
    convert: function (match, nosign) {
        if (nosign) {
            match.sign = '';
        } else {
            match.sign = match.negative ? '-' : match.sign;
        }
        var l = match.min - match.argument.length + 1 - match.sign.length;
        var pad = new Array(l < 0 ? 0 : l).join(match.pad);
        if (!match.left) {
            if (match.pad == "0" || nosign) {
                return match.sign + pad + match.argument;
            } else {
                return pad + match.sign + match.argument;
            }
        } else {
            if (match.pad == "0" || nosign) {
                return match.sign + match.argument + pad.replace(/0/g, ' ');
            } else {
                return match.sign + match.argument + pad;
            }
        }
    }
};

sprintf = sprintfWrapper.init;

function format_video_time(seconds) {
    const second = seconds % 60;
    const minute = Math.floor(seconds / 60.0) % 60;
    const hour = Math.floor(seconds / 3600.0);
    return sprintf("%d:%02d:%02d", hour, minute, second);
}


/**
 * 转全角字符
 */
function toDBC(str) {
    var result = "";
    var len = str.length;
    for (var i = 0; i < len; i++) {
        var cCode = str.charCodeAt(i);
        //全角与半角相差（除空格外）：65248(十进制)
        cCode = (cCode >= 0x0021 && cCode <= 0x007E) ? (cCode + 65248) : cCode;
        //处理空格
        cCode = (cCode == 0x0020) ? 0x03000 : cCode;
        result += String.fromCharCode(cCode);
    }
    return result;
}

/**
 * 转半角字符
 */
function toSBC(str) {
    var result = "";
    var len = str.length;
    for (var i = 0; i < len; i++) {
        var cCode = str.charCodeAt(i);
        //全角与半角相差（除空格外）：65248（十进制）
        cCode = (cCode >= 0xFF01 && cCode <= 0xFF5E) ? (cCode - 65248) : cCode;
        //处理空格
        cCode = (cCode == 0x03000) ? 0x0020 : cCode;
        result += String.fromCharCode(cCode);
    }
    return result;
}

function close_window() {
    window.opener = null;
    window.open('', '_self');
    window.close();
}

function notify_fail(text) {
    $.notify({
        // options
        icon: 'glyphicon glyphicon-exclamation-sign',
        message: text
    }, {
        // settings
        type: 'danger',
        placement: {
            from: "bottom",
            align: "right"
        },
    });
}

function notify_success(text) {
    $.notify({
        // options
        icon: 'glyphicon glyphicon-ok-sign',
        message: text
    }, {
        // settings
        type: 'info',
        placement: {
            from: "bottom",
            align: "right"
        },
    });
}