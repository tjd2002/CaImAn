pipeline {
  agent none
  options {
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '10', daysToKeepStr: '15'))
    timeout(time: 1, unit: 'HOURS')
    retry(3)
    timestamps()
  }
  stages {
    stage('test') {
      parallel {
        stage('linux-python2') {
          agent {
            dockerfile {
              dir "test/linux-python2"
              args '-v /etc/passwd:/etc/passwd -v /etc/group:/etc/group -v /home/jenkins/.conda2/pkgs:/home/jenkins/.conda/pkgs:rw,z'
            }
          }
          environment {
            CONDA_ENV = "${env.WORKSPACE}/test/${env.STAGE_NAME}"
          }
          steps {
            sh 'conda env create -q -f environment_python2.yml -p $CONDA_ENV'
            sh '''#!/bin/bash -ex
              source $CONDA_ENV/bin/activate $CONDA_ENV
              pip install .
              TEMPDIR=$(mktemp -d)
              export CAIMAN_DATA=$TEMPDIR/caiman_data
              cd $TEMPDIR
              caimanmanager.py install
              nosetests --traverse-namespace caiman
              caimanmanager.py demotest
            '''
          }
        }
        stage('linux-python3') {
          agent {
            dockerfile {
              dir "test/linux-python3"
              args '-v /etc/passwd:/etc/passwd -v /etc/group:/etc/group -v /home/jenkins/.conda3/pkgs:/home/jenkins/.conda/pkgs:rw,z'
            }
          }
          environment {
            CONDA_ENV = "${env.WORKSPACE}/test/${env.STAGE_NAME}"
          }
          steps {
            sh 'conda env create -q -f environment.yml -p $CONDA_ENV'
            sh '''#!/bin/bash -ex
              source $CONDA_ENV/bin/activate $CONDA_ENV
              pip install .
              TEMPDIR=$(mktemp -d)
              export CAIMAN_DATA=$TEMPDIR/caiman_data
              cd $TEMPDIR
              caimanmanager.py install
              nosetests --traverse-namespace caiman
              caimanmanager.py demotest
            '''
          }
        }

        stage('osx-python2') {
          agent {
            label 'osx && anaconda2'
          }
          environment {
            CONDA_ENV = "${env.WORKSPACE}/test/${env.STAGE_NAME}"
          }
          steps {
            sh '$ANACONDA2/bin/conda env create -q -f environment_python2.yml -p $CONDA_ENV'
            sh '''#!/bin/bash -ex
              source $ANACONDA2/bin/activate $CONDA_ENV
              pip install .
              TEMPDIR=$(mktemp -d)
              export CAIMAN_DATA=$TEMPDIR/caiman_data
              cd $TEMPDIR
              caimanmanager.py install
              nosetests --traverse-namespace caiman
            '''
          }
        }
        stage('osx-python3') {
          agent {
            label 'osx && anaconda3'
          }
          environment {
            CONDA_ENV = "${env.WORKSPACE}/test/${env.STAGE_NAME}"
            LANG = "en_US.UTF-8"
          }
          steps {
            sh '$ANACONDA3/bin/conda env create -q -f environment.yml -p $CONDA_ENV'
            sh '''#!/bin/bash -ex
              source $ANACONDA3/bin/activate $CONDA_ENV
              pip install .
              TEMPDIR=$(mktemp -d)
              export CAIMAN_DATA=$TEMPDIR/caiman_data
              cd $TEMPDIR
              caimanmanager.py install
              nosetests --traverse-namespace caiman
            '''
          }
        }

        stage('win-python3') {
          agent {
            label 'windows && anaconda3'
          }
          environment {
            CONDA_ENV = "${env.WORKSPACE}\\test\\${env.STAGE_NAME}"
          }
          steps {
            bat '%ANACONDA3%\\scripts\\conda info'
            bat '%ANACONDA3%\\scripts\\conda env create -q -f environment.yml -p %CONDA_ENV%'
            bat '%ANACONDA3%\\scripts\\activate %CONDA_ENV% && pip install . && copy caimanmanager.py %TEMP% && cd %TEMP% && set "CAIMAN_DATA=%TEMP%\\caiman_data" && (if exist caiman_data (rmdir caiman_data /s /q) else (echo "Host is fresh")) && python caimanmanager.py install && python caimanmanager.py test'
          }
        }
      }
    }
  }
  post {
    failure {
      emailext subject: '$PROJECT_NAME - Build # $BUILD_NUMBER - $BUILD_STATUS',
	       body: '''$PROJECT_NAME - Build # $BUILD_NUMBER - $BUILD_STATUS

Check console output at $BUILD_URL to view full results.

Building $BRANCH_NAME for $CAUSE
$JOB_DESCRIPTION

Chages:
$CHANGES

End of build log:
${BUILD_LOG,maxLines=60}
''',
	       recipientProviders: [
		 [$class: 'DevelopersRecipientProvider'],
	       ], 
	       replyTo: '$DEFAULT_REPLYTO',
	       to: 'epnevmatikakis@gmail.com, andrea.giovannucci@gmail.com, pgunn@flatironinstitute.org'
    }
  }
}
