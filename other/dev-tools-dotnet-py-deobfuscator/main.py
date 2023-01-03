import re 
import codecs 
import argparse
import base64
import os 

MATCH_VAR = re.compile(r"^([a-z_](?:[a-z_0-9]+)?)\s*=\s*(.*)$", re.IGNORECASE)

def decode_xt_str(value: str, *, XT_STR_FORMAT_MATCH = re.compile(r"((?:\\x[\da-zA-Z]{2}))|(.)")):

    """
        Converts a string encoded as something like \\x72\\x6f\\x74\\x31\\x33 its readable value
    """

    return "".join(chr(int(xt[2:], 16)) if xt else c for (xt, c) in XT_STR_FORMAT_MATCH.findall(value))
   

def strip_both_sides_until(value: str, until: list[str]):
    """
        removes everything on either side of the string until a value in the list is found

        removes the value in the list from the string as well

        this is used to remove brackets and ' and " 
        
        Example:
        ```
        # some function call string, we want only the value of the arg
        value = 'foo(  "lX3RleHQoYmFzZTY0LmI2NGR")'

        # since it could have ' or " we put both
        strip_both_sides_until(value, ['"', "'"])
        ```
    """
    length = len(value)

    i = 0

    while i < length and value[i] not in until:
        i += 1

    value = value[i + 1:]

    length = len(value)

    i = length - 1

    while i >= 0 and value[i] not in until:
        i -= 1

    return value[0:i]


def bracket_start_end_parse(value: str):

    bracket_count = 0

    start = -1
    
    for (i, c) in enumerate(value):

        if c == '(':

            if start == -1:
                start = i 

            bracket_count += 1

        elif c == ')':
            bracket_count -= 1

        if bracket_count == 0:
            break 

    if bracket_count != 0:
        return -1, -1

    return start, i


def get_codec_decode(value: str):
    
    start = value.find("codecs.decode")

    if start == -1:
        return ""

    call = value[start + 13:].strip()

    start, end = bracket_start_end_parse(call)

    if end == -1 or start == -1:
        return ""

    arg1, _, arg2 = call[start:end].partition(',')

    arg1 = strip_both_sides_until(arg1, ['"', "'"])
    arg2 = strip_both_sides_until(arg2, ['"', "'"])

    return codecs.decode(arg1, arg2)


def get_eval_expr(value: str):

    """
        Gets the start, length and value of an eval function call as a str (assuming only 1 argument)
    """

    start = value.find("eval")

    if start == -1:
        return (-1, -1, "")

    call = value[start+4:].strip()

    start, end = bracket_start_end_parse(call)

    if end == -1 or start == -1:
        return (-1, -1, "")

    return (start, end + 4, strip_both_sides_until(call[start:end], ['"', "'"]))


def decode_file(path: str, output_path: str):

    vars = []

    with open(path, "r") as reader:

        for line in reader:

            is_var = MATCH_VAR.match(line)
            
            if is_var:

                var = is_var.group(1)
                value = is_var.group(2)

                # removes ' and " if on either side 
                if len(value) > 1 and value[0] == value[-1] and value[0] in ('"', "'"):

                    value = value[1:-1]

                vars.append( [var, decode_xt_str(value)] )
                
                continue

    vars_dict = dict(vars)
    length = len(vars)

    with open(output_path, "wb") as writer:

        for (i, (var, value)) in enumerate(vars):

            # sub vars into each line
            for var2, value2 in vars_dict.items():

                if var2 == var: 
                    break 
                
                # yeah this is dumb, but who cares
                value2 = "'" + value2 + "'"
                vars[i][1] = vars[i][1].replace("'" + var2 + "'", value2) \
                                    .replace('"' + var2 + '"', value2) \
                                    .replace(var2, value2)

            value = vars[i][1]

            # update the dict to our newly subbed value 
            vars_dict[var] = value 

            token = []

            while True:

                start, length, expr = get_eval_expr(value)

                if start == -1:
                    break 

                if expr in vars_dict:

                    token.append(vars_dict[expr])

                else:
                    token.append(expr)

                decoded = get_codec_decode(token[-1])

                if decoded:

                    token[-1] = decoded

                value = value[start + length + 1:]


            if token:

                writer.write(base64.b64decode("".join(token)))


def main():
    
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION]... URL...",
        add_help=False,
    )

    general = parser.add_argument_group("General Options")
    general.add_argument(
        "-h", "--help",
        action="help",
        help="Print this help message and exit",
    )
    general.add_argument(
        "-i", "--input",
        dest="inputs", metavar="FILE", action="append",
        help="Specify input file. multiple -i can specified"
    )
    general.add_argument(
        "-o", "--output",
        dest="outputs", metavar="FILE", action="append",
        help="Specify the output file. multiple -i can specified"
    )

    args = parser.parse_args()

    if not args.inputs:
        parser.error("No input files given")

    if not args.outputs:
        args.ouputs = [i + ".deob.txt" for i in args.inputs]

    inputs = args.inputs
    outputs = args.outputs
    
    for i, path in enumerate(inputs):

        if i >= len(outputs):
            out = path + ".deob.txt"
        else:
            out = outputs[i]

        if os.path.isfile(path):

            decode_file(path, out)
        else:
            print(f"File {path} does not exist")



if __name__ == "__main__":
    main()

