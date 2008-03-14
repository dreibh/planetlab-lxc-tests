#include <stdio.h>
#include <sys/select.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

int main()
{
  FILE *fp = NULL, *fp_in = NULL;
  FILE *out_fp = NULL, *diff_fp = NULL;
  const char* topcmd = "/vservers/pl_netflow/vsys/test.out";
  const char* top_in_file = "/vservers/pl_netflow/vsys/test.in";
  char buf[4096];
  int fd_in = -1, fd_out;
  int res;
  int flag;
  int count = 1;
  struct timeval tv={.tv_sec=5,.tv_usec=0};

  while (count < 100) {
    fd_set readSet;
    int res;
    int nlines=0;

    printf("(.)", count);

    if ((fd_out = open(topcmd, O_RDONLY | O_NONBLOCK)) < 0) {
      fprintf(stderr, "error executing top\n");
      exit(-1);
    }
    if ((fd_in = open(top_in_file, O_WRONLY)) < 0) {
      fprintf(stderr, "error opening %s\n", top_in_file);
      exit(-1);
    }

    if ((flag = fcntl(fd_out, F_GETFL)) == -1) {
      printf("fcntl get failed\n");
      exit(-1);
    }

    FD_ZERO(&readSet);
    FD_SET(fd_out, &readSet);

    res = select(fd_out + 1, &readSet, NULL, NULL, &tv);
    if (res < 1) {
      printf("select failed\n");
      exit(-1);
    }

    if (fcntl(fd_out, F_SETFL, flag & ~O_NONBLOCK) == -1) {
      printf("fcntl set failed\n");
      exit(-1);
    }

    if ((flag = fcntl(fd_out, F_GETFL)) == -1) {
      printf("fcntl get failed\n");
      exit(-1);
    }

    if (flag & O_NONBLOCK == 0) {
      printf("fd_out still nonblocking\n");
      exit(-1);
    }

    if ((fp = fdopen(fd_out, "r")) == NULL) {
      printf("fdopen failed\n");
      exit(-1);
    }

    if ((out_fp = fopen("/tmp/vsys_passwd_test", "w")) == NULL) {
	    printf("could not create tmp file for test\n");
            exit(-1);
    }

    while (fgets(buf, sizeof(buf), fp) != NULL) {
	fprintf(out_fp, "%s",buf);
    }

    fflush(out_fp);
    fclose(out_fp);

    if ((diff_fp = popen("/usr/bin/diff -u /tmp/vsys_passwd_test /etc/passwd","r")) == NULL) {
	    printf("Could not diff results\n");
	    exit(-1);
    }

    while (fgets(buf, sizeof(buf), diff_fp) != NULL) {
	    nlines++;
    }

    if (nlines) {
	    printf("Test returned different results - run again to verify\n");
	    exit(-1);
    }

    pclose (diff_fp);
    fclose(fp);
    close(fd_in);
    count++;
  }
  printf("test successful.\n");
  exit(0);

}
