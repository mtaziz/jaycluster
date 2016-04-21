# -*- coding:utf-8 -*-

def get_line_count(count, src_filename="ASIN", dic_filename="result"):
    f_in = open("%s.txt"%src_filename, "r")
    f_out = open("%s.txt"%dic_filename, "w")
#    f_in.readline()
    for i in range(int(count)):
	f_out.write(f_in.readline())

    f_out.close()
    f_in.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv)>2:
        get_line_count(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        get_line_count(sys.argv[1])
