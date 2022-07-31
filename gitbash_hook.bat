@REM provide bash file as command argument when executing batch file
@REM i.e. get_dpn_data.bash, plot_weekly_spc.bash

IF [%1]==[] EXIT

ECHO %1

SET GITBASH=C:\Users\daronphang\AppData\Local\Programs\Git\git-bash.exe
SET PARENTDIR=C:\Users\daronphang\coding_projects\pee_df_adhoc_requests

cd /d %PARENTDIR%
"%GITBASH%" -c "bash %1" 
@REM "%GITBASH%" --login -i -c "pwd; exec /bin/bash" 
@REM "%GITBASH%" --login -i -c "cd %PARENTDIR%" "bash %1" 